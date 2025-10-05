"""
Complete backtest example for Strategy1 with synthetic data.

This script demonstrates a full backtest setup using generated data.
In production, replace the synthetic data with real historical data.
"""

import random
from datetime import datetime, timedelta
from decimal import Decimal

from nautilus_trader.backtest.engine import BacktestEngine, BacktestEngineConfig
from nautilus_trader.backtest.models import FillModel
from nautilus_trader.backtest.modules import FXRolloverInterestModule
from nautilus_trader.common.enums import LogLevel
from nautilus_trader.model.currencies import USD, BTC
from nautilus_trader.model.data import Bar, BarType
from nautilus_trader.model.enums import (
    AccountType,
    AggregationSource,
    BarAggregation,
    OmsType,
    PriceType,
)
from nautilus_trader.model.identifiers import InstrumentId, Symbol, Venue, ClientId
from nautilus_trader.model.instruments import CryptoPerpetual
from nautilus_trader.model.objects import Money, Price, Quantity
from nautilus_trader.core.datetime import dt_to_unix_nanos

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bot.bot1 import Strategy1, Strategy1Config


def generate_synthetic_bars(
    instrument_id: InstrumentId,
    bar_type: BarType,
    start_price: float = 50000.0,
    num_bars: int = 1000,
    start_time: datetime = None,
) -> list[Bar]:
    """
    Generate synthetic bar data for backtesting.
    
    Parameters
    ----------
    instrument_id : InstrumentId
        The instrument identifier
    bar_type : BarType
        The bar type specification
    start_price : float
        Starting price for the synthetic data
    num_bars : int
        Number of bars to generate
    start_time : datetime, optional
        Start time for the data
        
    Returns
    -------
    list[Bar]
        List of generated bars
    """
    if start_time is None:
        start_time = datetime(2024, 1, 1, 0, 0, 0)
    
    bars = []
    current_price = start_price
    current_time = start_time
    
    # Create a trending market with some noise
    trend = 1  # 1 for uptrend, -1 for downtrend
    bars_in_trend = 0
    trend_duration = random.randint(50, 150)
    
    for i in range(num_bars):
        # Switch trend periodically
        if bars_in_trend > trend_duration:
            trend *= -1
            bars_in_trend = 0
            trend_duration = random.randint(50, 150)
        
        bars_in_trend += 1
        
        # Generate OHLC with trend and noise
        trend_change = random.uniform(0.0005, 0.002) * trend
        noise = random.uniform(-0.001, 0.001)
        
        open_price = current_price
        close_price = current_price * (1 + trend_change + noise)
        
        # Generate high and low
        high_offset = random.uniform(0.001, 0.003)
        low_offset = random.uniform(0.001, 0.003)
        
        high_price = max(open_price, close_price) * (1 + high_offset)
        low_price = min(open_price, close_price) * (1 - low_offset)
        
        # Create bar
        ts_init = dt_to_unix_nanos(current_time)
        ts_event = ts_init
        
        bar = Bar(
            bar_type=bar_type,
            open=Price.from_str(f"{open_price:.2f}"),
            high=Price.from_str(f"{high_price:.2f}"),
            low=Price.from_str(f"{low_price:.2f}"),
            close=Price.from_str(f"{close_price:.2f}"),
            volume=Quantity.from_int(random.randint(100, 10000)),
            ts_event=ts_event,
            ts_init=ts_init,
        )
        
        bars.append(bar)
        
        # Update for next bar
        current_price = close_price
        current_time += timedelta(minutes=15)  # 15-minute bars
    
    return bars


def run_backtest():
    """
    Run a complete backtest with Strategy1.
    """
    print("=" * 80)
    print("Running Strategy1 Backtest")
    print("=" * 80)
    print()
    
    # Define instrument
    venue = Venue("BINANCE")
    symbol = Symbol("BTCUSDT-PERP")
    instrument_id = InstrumentId(symbol=symbol, venue=venue)
    
    # Create instrument
    instrument = CryptoPerpetual(
        instrument_id=instrument_id,
        raw_symbol=symbol,
        base_currency=BTC,
        quote_currency=USD,
        settlement_currency=USD,
        is_inverse=False,
        price_precision=2,
        size_precision=3,
        price_increment=Price.from_str("0.01"),
        size_increment=Quantity.from_str("0.001"),
        max_quantity=Quantity.from_str("1000.0"),
        min_quantity=Quantity.from_str("0.001"),
        max_price=Price.from_str("1000000.0"),
        min_price=Price.from_str("0.01"),
        margin_init=Decimal("0.1"),
        margin_maint=Decimal("0.05"),
        maker_fee=Decimal("0.0002"),
        taker_fee=Decimal("0.0004"),
        ts_event=0,
        ts_init=0,
    )
    
    # Define bar type
    bar_type = BarType(
        instrument_id=instrument_id,
        bar_spec=BarType.parse("15-MINUTE-LAST"),
        aggregation_source=AggregationSource.EXTERNAL,
    )
    
    # Generate synthetic data
    print("Generating synthetic market data...")
    bars = generate_synthetic_bars(
        instrument_id=instrument_id,
        bar_type=bar_type,
        start_price=50000.0,
        num_bars=1000,
    )
    print(f"Generated {len(bars)} bars")
    print(f"Date range: {bars[0].ts_init.as_datetime()} to {bars[-1].ts_init.as_datetime()}")
    print(f"Price range: ${bars[0].open} to ${bars[-1].close}")
    print()
    
    # Configure backtest engine
    config = BacktestEngineConfig(
        logging=LogLevel.INFO,
    )
    
    engine = BacktestEngine(config=config)
    
    # Add venue
    engine.add_venue(
        venue=venue,
        oms_type=OmsType.NETTING,
        account_type=AccountType.MARGIN,
        base_currency=USD,
        starting_balances=[Money(100000, USD)],
    )
    
    # Add instrument
    engine.add_instrument(instrument)
    
    # Add data
    engine.add_bars(bars)
    
    # Configure strategy
    strategy_config = Strategy1Config(
        instrument_id=str(instrument_id),
        bar_type=str(bar_type),
        ema_periods=[20, 50, 100, 200],
        macd_fast_period=12,
        macd_slow_period=26,
        macd_signal_period=9,
        risk_percent=0.01,
        stop_loss_atr_multiplier=2.0,
        take_profit_risk_reward=2.0,
    )
    
    # Add strategy
    strategy = Strategy1(config=strategy_config)
    engine.add_strategy(strategy)
    
    print("Strategy Configuration:")
    print(f"  Instrument: {strategy_config.instrument_id}")
    print(f"  Bar Type: {strategy_config.bar_type}")
    print(f"  EMA Periods: {strategy_config.ema_periods}")
    print(f"  MACD: {strategy_config.macd_fast_period}/{strategy_config.macd_slow_period}/{strategy_config.macd_signal_period}")
    print(f"  Risk per trade: {strategy_config.risk_percent * 100}%")
    print()
    
    # Run backtest
    print("=" * 80)
    print("Running backtest...")
    print("=" * 80)
    print()
    
    engine.run()
    
    print()
    print("=" * 80)
    print("Backtest Complete")
    print("=" * 80)
    print()
    
    # Get results
    account = engine.trader.generate_account_report(venue)
    print("Account Report:")
    print(account)
    print()
    
    positions = engine.trader.generate_positions_report()
    if positions:
        print("Positions Report:")
        print(positions)
        print()
    
    orders = engine.trader.generate_orders_report()
    if orders:
        print("Orders Report:")
        print(orders)
        print()
    
    fills = engine.trader.generate_order_fills_report()
    if fills:
        print("Fills Report:")
        print(fills)
        print()
    
    print("=" * 80)
    print()


if __name__ == "__main__":
    run_backtest()

