__doc__ = """
Bot 1 Trading Strategy - Multi-Indicator Strategy
Combines:
- Pivot Points (Camarilla) for support/resistance levels
- EMA (Exponential Moving Average) for trend identification
- MACD (Moving Average Convergence Divergence) for momentum signals

Strategy Logic:
- Enter LONG when: uptrend (EMA), bullish MACD crossover, price near Pivot Points PP
- Enter SHORT when: downtrend (EMA), bearish MACD crossover, price near Pivot Points PP
- Exit using stop loss and take profit based on pivot point levels
"""

from decimal import Decimal
from typing import Optional

from msgspec import field

from nautilus_trader.config import StrategyConfig
from nautilus_trader.core.datetime import unix_nanos_to_dt
from nautilus_trader.core.message import Event
from nautilus_trader.model.data import Bar, BarType
from nautilus_trader.model.enums import OrderSide, PositionSide
from nautilus_trader.model.identifiers import InstrumentId
from nautilus_trader.model.instruments import Instrument
from nautilus_trader.trading.strategy import Strategy

from bot.ema_indicator import MultiEMAIndicator
from bot.macd_indicator import MACDIndicator
from bot.pivot_point import CamarillaPivotPoints


class Strategy1Config(StrategyConfig, frozen=True):
    """
    Configuration for Strategy1.
    
    Parameters
    ----------
    instrument_id : InstrumentId
        The instrument ID to trade
    bar_type : BarType
        The bar type for the strategy
    ema_periods : list[int]
        EMA periods to use (e.g., [20, 50, 100, 200])
    macd_fast_period : int
        MACD fast EMA period (default: 12)
    macd_slow_period : int
        MACD slow EMA period (default: 26)
    macd_signal_period : int
        MACD signal line period (default: 9)
    risk_percent : float
        Risk percentage per trade (default: 0.01 = 1%)
    stop_loss_atr_multiplier : float
        Stop loss multiplier based on ATR (default: 2.0)
    take_profit_risk_reward : float
        Take profit ratio relative to stop loss (default: 2.0 = 2:1 R/R)
    """
    instrument_id: str
    bar_type: str
    ema_periods: list[int] = field(default_factory=lambda: [20, 50, 100, 200])
    macd_fast_period: int = 13
    macd_slow_period: int = 34
    macd_signal_period: int = 9
    risk_percent: float = 0.01
    stop_loss_atr_multiplier: float = 2.0
    take_profit_risk_reward: float = 2.0


class Strategy1(Strategy):
    """
    Multi-indicator trading strategy using EMA, MACD, and Pivot Points.
    
    This strategy combines trend following (EMA), momentum (MACD), and 
    support/resistance (Pivot Points) to generate trading signals.
    """
    
    def __init__(self, config: Strategy1Config) -> None:
        """
        Initialize the strategy.
        
        Parameters
        ----------
        config : Strategy1Config
            The strategy configuration
        """
        super().__init__(config)
        
        # Configuration
        self.instrument_id = InstrumentId.from_str(config.instrument_id)
        self.bar_type = BarType.from_str(config.bar_type)
        
        # Indicators
        self.ema_indicator = MultiEMAIndicator(periods=config.ema_periods)
        self.macd_indicator = MACDIndicator(
            fast_period=config.macd_fast_period,
            slow_period=config.macd_slow_period,
            signal_period=config.macd_signal_period
        )
        self.pivot_points = CamarillaPivotPoints(timeframe="15")  # 15-minute timeframe
        
        # Price history for indicators
        self.price_history: list[float] = []
        self.high_history: list[float] = []
        self.low_history: list[float] = []
        
        # Trading parameters
        self.risk_percent = config.risk_percent
        self.stop_loss_atr_multiplier = config.stop_loss_atr_multiplier
        self.take_profit_risk_reward = config.take_profit_risk_reward
        
        # State
        self.instrument: Optional[Instrument] = None
        
    def on_start(self) -> None:
        """
        Actions to be performed when the strategy is started.
        """
        self.instrument = self.cache.instrument(self.instrument_id)
        if self.instrument is None:
            self.log.error(f"Could not find instrument for {self.instrument_id}")
            self.stop()
            return
        
        # Subscribe to data
        self.subscribe_bars(self.bar_type)
        
        self.log.info(f"Strategy started for {self.instrument_id}")
        self.log.info(f"EMA periods: {self.ema_indicator.periods}")
        self.log.info(f"MACD: {self.macd_indicator.fast_period}/{self.macd_indicator.slow_period}/{self.macd_indicator.signal_period}")
    
    def on_stop(self) -> None:
        """
        Actions to be performed when the strategy is stopped.
        """
        # Close any open positions
        self.close_all_positions(self.instrument_id)
        
        # Unsubscribe from data
        self.unsubscribe_bars(self.bar_type)
        
        self.log.info("Strategy stopped")
    
    def on_bar(self, bar: Bar) -> None:
        """
        Process a new bar.
        
        Parameters
        ----------
        bar : Bar
            The bar to process
        """
        # Update price history
        self.price_history.append(float(bar.close))
        self.high_history.append(float(bar.high))
        self.low_history.append(float(bar.low))
        
        # Keep only the last 300 bars (enough for longest EMA + some buffer)
        max_history = 300
        if len(self.price_history) > max_history:
            self.price_history = self.price_history[-max_history:]
            self.high_history = self.high_history[-max_history:]
            self.low_history = self.low_history[-max_history:]
        
        # Update pivot points
        # for pivot points(15m) we can update for every day, no need every bar
        self.pivot_points.update(
            timestamp=unix_nanos_to_dt(bar.ts_init),
            high=float(bar.high),
            low=float(bar.low),
            close=float(bar.close)
        )
        
        # Wait for enough data
        min_required_bars = max(self.ema_indicator.periods) + 10
        if len(self.price_history) < min_required_bars:
            self.log.info(f"Collecting data... {len(self.price_history)}/{min_required_bars}")
            return
        
        # Check if we already have a position
        if self.portfolio.is_flat(self.instrument_id):
            # Look for entry signals
            self._check_entry_signals(bar)
        else:
            # Manage existing position
            self._manage_position(bar)
    
    def _check_entry_signals(self, bar: Bar) -> None:
        """
        Check for entry signals.
        
        Parameters
        ----------
        bar : Bar
            Current bar
        """
        current_price = float(bar.close)
        
        # Check EMA trend
        is_uptrend = self.ema_indicator.is_trend_up(self.price_history)
        
        # Check MACD signals
        # is_macd_bullish = self.macd_indicator.is_bullish_crossover(self.price_history)
        # is_macd_bearish = self.macd_indicator.is_bearish_crossover(self.price_history)
        
        # Get pivot points
        pivots = self.pivot_points.pivot_points
        
        # Long entry conditions
        if is_uptrend:
            # Check if price is near support level (within 0.5% of pp)
            if pivots['pp'] is not None:
                near_pp = abs(current_price - pivots['pp']) / current_price < 0.005
                
                if near_pp:
                    self.log.info(f"LONG signal detected at {current_price}")
                    self._enter_long(bar)
        
        # Short entry conditions
        elif not is_uptrend:
            # Check if price is near resistance level (within 0.5% of pp)
            if pivots['pp'] is not None:
                near_pp = abs(current_price - pivots['pp']) / current_price < 0.005
                
                if near_pp:
                    self.log.info(f"SHORT signal detected at {current_price}")
                    self._enter_short(bar)
    
    def _enter_long(self, bar: Bar) -> None:
        """
        Enter a long position.
        
        Parameters
        ----------
        bar : Bar
            Current bar
        """
        if self.instrument is None:
            return
        
        # Calculate position size
        quantity = self._calculate_position_size(bar)
        
        # Create market order
        order = self.order_factory.market(
            instrument_id=self.instrument_id,
            order_side=OrderSide.BUY,
            quantity=quantity,
        )
        
        self.submit_order(order)
        self.log.info(f"Submitted LONG order: {quantity} @ {bar.close}")
    
    def _enter_short(self, bar: Bar) -> None:
        """
        Enter a short position.
        
        Parameters
        ----------
        bar : Bar
            Current bar
        """
        if self.instrument is None:
            return
        
        # Calculate position size
        quantity = self._calculate_position_size(bar)
        
        # Create market order
        order = self.order_factory.market(
            instrument_id=self.instrument_id,
            order_side=OrderSide.SELL,
            quantity=quantity,
        )
        
        self.submit_order(order)
        self.log.info(f"Submitted SHORT order: {quantity} @ {bar.close}")
    
    def _calculate_position_size(self, bar: Bar) -> Decimal:
        """
        Calculate position size based on risk management.
        
        Parameters
        ----------
        bar : Bar
            Current bar
        
        Returns
        -------
        Decimal
            Position size
        """
        if self.instrument is None:
            return Decimal("0.01")
        
        # Simple position sizing: use minimum size for demo
        # In production, calculate based on account balance and risk
        return self.instrument.make_qty(0.01)
    
    def _manage_position(self, bar: Bar) -> None:
        """
        Manage existing position (trailing stop, take profit, etc.).
        
        Parameters
        ----------
        bar : Bar
            Current bar
        """
        # Get current position using cache
        positions = [p for p in self.cache.positions() if p.instrument_id == self.instrument_id and p.is_open]
        if not positions:
            return
        
        position = positions[0]
        
        current_price = float(bar.close)
        entry_price = float(position.avg_px_open)
        
        # Calculate profit/loss percentage
        if position.side == PositionSide.LONG:
            pnl_pct = (current_price - entry_price) / entry_price
        else:
            pnl_pct = (entry_price - current_price) / entry_price
        
        # Exit conditions
        should_exit = False
        exit_reason = ""
        
        # Stop loss: -2%
        if pnl_pct <= -0.01:
            should_exit = True
            exit_reason = "Stop Loss"
        
        # Take profit: +4% (2:1 risk/reward)
        elif pnl_pct >= 0.02:
            should_exit = True
            exit_reason = "Take Profit"
        
        # Opposite MACD signal
        elif position.side == PositionSide.LONG and self.macd_indicator.is_bearish_crossover(self.price_history):
            should_exit = True
            exit_reason = "MACD Reversal"
        elif position.side == PositionSide.SHORT and self.macd_indicator.is_bullish_crossover(self.price_history):
            should_exit = True
            exit_reason = "MACD Reversal"
        
        if should_exit:
            self.log.info(f"Exiting position: {exit_reason} (PnL: {pnl_pct*100:.2f}%)")
            self.close_position(position)
    
    def on_event(self, event: Event) -> None:
        """
        Handle events.
        
        Parameters
        ----------
        event : Event
            The event to handle
        """
        pass
