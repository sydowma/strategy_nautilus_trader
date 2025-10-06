"""
Funding Rate Arbitrage Strategy

This strategy implements a cash-and-carry arbitrage by:
1. Buying spot (going LONG on spot)
2. Shorting perpetual futures (going SHORT on futures)
3. Collecting positive funding rates (shorts receive funding from longs)

The positions are fully hedged, so profit comes purely from funding rate收益.
"""

from decimal import Decimal
from nautilus_trader.config import StrategyConfig
from nautilus_trader.core.correctness import PyCondition
from nautilus_trader.model.data import Bar, BarType
from nautilus_trader.model.enums import OrderSide, PositionSide
from nautilus_trader.model.identifiers import InstrumentId
from nautilus_trader.model.instruments import Instrument
from nautilus_trader.model.orders import MarketOrder
from nautilus_trader.trading.strategy import Strategy

from tools.funding_rate_simulator import FundingRateData, FundingRateTracker


class FundingArbitrageConfig(StrategyConfig, frozen=True):
    """
    Configuration for Funding Arbitrage Strategy
    
    Parameters
    ----------
    spot_instrument_id : str
        Spot instrument ID (e.g., "BTCUSDT.BINANCE")
    futures_instrument_id : str
        Perpetual futures instrument ID (e.g., "BTCUSDT-PERP.BINANCE")
    bar_type : str
        Bar type for data subscription
    funding_rate_threshold : float
        Minimum funding rate to open position (e.g., 0.0005 = 0.05%)
    exit_funding_rate : float
        Funding rate below which to close position (e.g., 0.0001 = 0.01%)
    position_size_usdt : float
        Position size in USDT for each side
    max_position_duration_hours : int
        Maximum hours to hold position (default 24)
    """
    
    spot_instrument_id: str
    futures_instrument_id: str
    bar_type: str
    funding_rate_threshold: float = 0.0005  # 0.05% per 8h
    exit_funding_rate: float = 0.0001  # 0.01% per 8h
    position_size_usdt: float = 1000.0
    max_position_duration_hours: int = 24
    

class FundingArbitrageStrategy(Strategy):
    """
    Funding Rate Arbitrage Strategy
    
    This strategy profits from positive funding rates by maintaining
    a market-neutral position (long spot + short futures).
    """
    
    def __init__(self, config: FundingArbitrageConfig):
        super().__init__(config=config)
        
        # Configuration
        self.spot_instrument_id = InstrumentId.from_str(config.spot_instrument_id)
        self.futures_instrument_id = InstrumentId.from_str(config.futures_instrument_id)
        self.funding_rate_threshold = config.funding_rate_threshold
        self.exit_funding_rate = config.exit_funding_rate
        self.position_size_usdt = config.position_size_usdt
        self.max_position_duration_hours = config.max_position_duration_hours
        
        # Strategy state
        self.is_position_open = False
        self.entry_time = None
        self.spot_position_size = 0.0
        self.futures_position_size = 0.0
        self.current_funding_rate = 0.0
        
        # Funding rate tracking
        self.funding_data: FundingRateData = None
        self.funding_tracker: FundingRateTracker = None
        
        # Performance tracking
        self.total_trades = 0
        self.total_funding_earned = 0.0
        self.total_fees_paid = 0.0
    
    def on_start(self):
        """
        Actions to be performed on strategy start
        """
        # Subscribe to data
        bar_type = BarType.from_str(self.config.bar_type)
        self.subscribe_bars(bar_type)
        
        self.log.info(f"Strategy started")
        self.log.info(f"Spot: {self.spot_instrument_id}")
        self.log.info(f"Futures: {self.futures_instrument_id}")
        self.log.info(f"Funding threshold: {self.funding_rate_threshold:.4f}%")
        self.log.info(f"Position size: ${self.position_size_usdt:,.2f}")
    
    def on_stop(self):
        """
        Actions to be performed on strategy stop
        """
        # Close any open positions
        if self.is_position_open:
            self.close_arbitrage_position("Strategy stopped")
        
        # Print funding summary
        if self.funding_tracker:
            self.funding_tracker.print_summary()
        
        self.log.info("Strategy stopped")
    
    def set_funding_data(self, funding_data: FundingRateData):
        """
        Set funding rate data for the strategy
        
        Parameters
        ----------
        funding_data : FundingRateData
            Historical funding rate data
        """
        self.funding_data = funding_data
        self.funding_tracker = FundingRateTracker(funding_data)
        self.log.info(f"Funding data loaded: {len(funding_data.rates)} records")
    
    def on_bar(self, bar: Bar):
        """
        Process bar data and make trading decisions
        
        Parameters
        ----------
        bar : Bar
            Bar data
        """
        # Get current timestamp
        current_time_ms = bar.ts_event // 1_000_000  # Convert nanoseconds to milliseconds
        
        # Update current funding rate
        if self.funding_data:
            rate = self.funding_data.get_rate_at(current_time_ms)
            if rate is not None:
                self.current_funding_rate = rate
        
        # Check if it's a funding settlement time
        is_settlement = (self.funding_data and 
                        self.funding_data.is_settlement_time(current_time_ms))
        
        if is_settlement and self.is_position_open:
            # Calculate and record funding payment
            # Get the futures position from open positions
            futures_position = next(
                (pos for pos in self.cache.positions_open() 
                 if pos.instrument_id == self.futures_instrument_id),
                None
            )
            if futures_position and futures_position.is_open:
                position_value = float(futures_position.quantity) * float(bar.close)
                funding = self.funding_tracker.calculate_funding(
                    timestamp_ms=current_time_ms,
                    position_size=float(futures_position.quantity),
                    position_value=position_value,
                    side='SHORT'
                )
                self.total_funding_earned += funding
                self.log.info(
                    f"💰 Funding settlement: ${funding:,.2f} "
                    f"(Rate: {self.current_funding_rate:.6f})"
                )
        
        # Trading logic
        if not self.is_position_open:
            self._check_entry_conditions(bar)
        else:
            self._check_exit_conditions(bar)
    
    def _check_entry_conditions(self, bar: Bar):
        """
        Check if conditions are met to open arbitrage position
        
        Parameters
        ----------
        bar : Bar
            Current bar data
        """
        # Only enter if funding rate is above threshold
        if self.current_funding_rate < self.funding_rate_threshold:
            return
        
        # Check if we have enough balance
        # In a real implementation, you'd check actual balances
        
        self.log.info(
            f"📈 Opening arbitrage position | "
            f"Funding rate: {self.current_funding_rate:.6f} "
            f"({self.current_funding_rate*100:.4f}%)"
        )
        
        # Open positions
        self.open_arbitrage_position(bar)
    
    def _check_exit_conditions(self, bar: Bar):
        """
        Check if conditions are met to close arbitrage position
        
        Parameters
        ----------
        bar : Bar
            Current bar data
        """
        # Exit if funding rate drops below exit threshold
        if self.current_funding_rate < self.exit_funding_rate:
            self.log.info(
                f"📉 Funding rate too low: {self.current_funding_rate:.6f} "
                f"< {self.exit_funding_rate:.6f}"
            )
            self.close_arbitrage_position("Funding rate too low")
            return
        
        # Exit if max duration exceeded
        if self.entry_time:
            current_time_ms = bar.ts_event // 1_000_000
            hours_held = (current_time_ms - self.entry_time) / (1000 * 3600)
            
            if hours_held > self.max_position_duration_hours:
                self.log.info(
                    f"⏰ Max duration exceeded: {hours_held:.1f}h "
                    f"> {self.max_position_duration_hours}h"
                )
                self.close_arbitrage_position("Max duration exceeded")
                return
    
    def open_arbitrage_position(self, bar: Bar):
        """
        Open hedged arbitrage position (long spot + short futures)
        
        Parameters
        ----------
        bar : Bar
            Current bar data
        """
        from nautilus_trader.model.orders import MarketOrder
        from nautilus_trader.model.enums import OrderSide, TimeInForce
        from decimal import Decimal
        
        current_price = float(bar.close)
        
        # Calculate position sizes
        position_size = self.position_size_usdt / current_price
        
        # Round to instrument precision
        instrument = self.cache.instrument(self.futures_instrument_id)
        if instrument:
            quantity = instrument.make_qty(Decimal(str(position_size)))
        else:
            quantity = Decimal(str(round(position_size, 4)))
        
        # Create and submit BOTH orders for hedged position:
        # 1. BUY spot (long)
        spot_order = self.order_factory.market(
            instrument_id=self.spot_instrument_id,
            order_side=OrderSide.BUY,  # Long spot
            quantity=quantity,
        )
        
        # 2. SELL futures (short)  
        futures_order = self.order_factory.market(
            instrument_id=self.futures_instrument_id,
            order_side=OrderSide.SELL,  # Short futures
            quantity=quantity,
        )
        
        # Submit both orders
        self.submit_order(spot_order)
        self.submit_order(futures_order)
        
        # Track state
        self.is_position_open = True
        self.entry_time = bar.ts_event // 1_000_000  # milliseconds
        self.spot_position_size = float(quantity)
        self.futures_position_size = float(quantity)
        
        self.total_trades += 1
        
        self.log.info(
            f"✅ Arbitrage opened | "
            f"Size: {quantity} | "
            f"Price: ${current_price:,.2f} | "
            f"Value: ${self.position_size_usdt:,.2f}"
        )
    
    def close_arbitrage_position(self, reason: str):
        """
        Close hedged arbitrage position
        
        Parameters
        ----------
        reason : str
            Reason for closing
        """
        if not self.is_position_open:
            return
        
        self.log.info(f"🔒 Closing arbitrage position | Reason: {reason}")
        
        # Get both open positions
        spot_position = next(
            (pos for pos in self.cache.positions_open() 
             if pos.instrument_id == self.spot_instrument_id),
            None
        )
        
        futures_position = next(
            (pos for pos in self.cache.positions_open() 
             if pos.instrument_id == self.futures_instrument_id),
            None
        )
        
        # Close both positions
        if spot_position and spot_position.is_open:
            self.close_position(spot_position)
            
        if futures_position and futures_position.is_open:
            self.close_position(futures_position)
        
        # Track state
        self.is_position_open = False
        self.entry_time = None
        self.spot_position_size = 0.0
        self.futures_position_size = 0.0
        
        # Print current P&L
        net_funding = self.funding_tracker.get_net_funding() if self.funding_tracker else 0
        self.log.info(
            f"📊 Position closed | "
            f"Net funding: ${net_funding:,.2f} | "
            f"Trades: {self.total_trades}"
        )
    
    def on_reset(self):
        """
        Reset the strategy state
        """
        self.is_position_open = False
        self.entry_time = None
        self.spot_position_size = 0.0
        self.futures_position_size = 0.0
        self.current_funding_rate = 0.0
        self.total_trades = 0
        self.total_funding_earned = 0.0
        self.total_fees_paid = 0.0
    
    def get_performance_summary(self) -> dict:
        """
        Get strategy performance summary
        
        Returns
        -------
        dict
            Performance metrics
        """
        funding_summary = {}
        if self.funding_tracker:
            funding_summary = self.funding_tracker.get_funding_summary()
        
        return {
            'total_trades': self.total_trades,
            'net_funding': funding_summary.get('net_funding', 0.0),
            'total_received': funding_summary.get('total_received', 0.0),
            'total_paid': funding_summary.get('total_paid', 0.0),
            'avg_funding_rate': funding_summary.get('avg_rate', 0.0),
            'total_settlements': funding_summary.get('total_settlements', 0),
        }

