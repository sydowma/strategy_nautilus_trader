"""
Run backtest with real EURUSD historical data.

This script uses the actual CSV data file to run a complete backtest
of Strategy1 with real market data.
"""

import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from decimal import Decimal

from nautilus_trader.backtest.engine import BacktestEngine, BacktestEngineConfig
from nautilus_trader.common.enums import LogLevel
from nautilus_trader.model.currencies import USD
from nautilus_trader.model.enums import AccountType, OmsType
from nautilus_trader.model.objects import Money

from bot.bot1 import Strategy1, Strategy1Config
from tools.load_csv_data import load_tick_data_from_csv, convert_ticks_to_bars, create_eurusd_instrument
from nautilus_trader.model.enums import AggregationSource
from nautilus_trader.model.data import BarType


def run_backtest_with_real_data():
    """
    Run backtest using real EURUSD data from CSV file.
    """
    print("=" * 80)
    print("Strategy1 Backtest with Real EURUSD Data")
    print("=" * 80)
    print()
    
    # Step 1: Load and process data
    print("Step 1: Loading historical data...")
    csv_file = "/Users/oker/GitHub/bot/strategy_nautilus_trader/DAT_ASCII_EURUSD_T_202001.csv.gz"
    
    # Load tick data
    df = load_tick_data_from_csv(csv_file)
    
    # Create instrument
    instrument = create_eurusd_instrument()
    venue = instrument.id.venue
    
    # Define bar type (15-minute bars)
    bar_type = BarType(
        instrument_id=instrument.id,
        bar_spec=BarType.parse("15-MINUTE-MID"),
        aggregation_source=AggregationSource.EXTERNAL,
    )
    
    # Convert ticks to bars
    bars = convert_ticks_to_bars(df, instrument.id, bar_type, freq='15min')
    
    print()
    print(f"Data loaded successfully:")
    print(f"  - Instrument: {instrument.id}")
    print(f"  - Bar type: {bar_type}")
    print(f"  - Total bars: {len(bars)}")
    print(f"  - Date range: {bars[0].ts_init.as_datetime()} to {bars[-1].ts_init.as_datetime()}")
    print()
    
    # Step 2: Configure backtest engine
    print("Step 2: Configuring backtest engine...")
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
        starting_balances=[Money(10000, USD)],  # Start with $10,000
    )
    
    # Add instrument
    engine.add_instrument(instrument)
    
    # Add bar data
    engine.add_bars(bars)
    
    print("Backtest engine configured")
    print(f"  - Starting balance: $10,000 USD")
    print(f"  - Account type: MARGIN")
    print()
    
    # Step 3: Configure and add strategy
    print("Step 3: Configuring trading strategy...")
    strategy_config = Strategy1Config(
        instrument_id=str(instrument.id),
        bar_type=str(bar_type),
        ema_periods=[20, 50, 100, 200],
        macd_fast_period=12,
        macd_slow_period=26,
        macd_signal_period=9,
        risk_percent=0.01,
        stop_loss_atr_multiplier=2.0,
        take_profit_risk_reward=2.0,
    )
    
    strategy = Strategy1(config=strategy_config)
    engine.add_strategy(strategy)
    
    print("Strategy configured:")
    print(f"  - EMA periods: {strategy_config.ema_periods}")
    print(f"  - MACD: {strategy_config.macd_fast_period}/{strategy_config.macd_slow_period}/{strategy_config.macd_signal_period}")
    print(f"  - Risk per trade: {strategy_config.risk_percent * 100}%")
    print(f"  - Stop Loss: -2% | Take Profit: +4%")
    print()
    
    # Step 4: Run backtest
    print("=" * 80)
    print("Running backtest...")
    print("=" * 80)
    print()
    
    engine.run()
    
    print()
    print("=" * 80)
    print("Backtest Complete!")
    print("=" * 80)
    print()
    
    # Step 5: Display results
    print("PERFORMANCE SUMMARY")
    print("=" * 80)
    
    # Account report
    account_report = engine.trader.generate_account_report(venue)
    print("\n📊 Account Report:")
    print("-" * 80)
    print(account_report)
    
    # Orders report
    orders_report = engine.trader.generate_orders_report()
    if orders_report:
        print("\n📝 Orders Report:")
        print("-" * 80)
        print(orders_report)
    else:
        print("\n📝 No orders were placed during the backtest")
    
    # Positions report
    positions_report = engine.trader.generate_positions_report()
    if positions_report:
        print("\n📈 Positions Report:")
        print("-" * 80)
        print(positions_report)
    else:
        print("\n📈 No positions were opened during the backtest")
    
    # Fills report
    fills_report = engine.trader.generate_order_fills_report()
    if fills_report:
        print("\n✅ Fills Report:")
        print("-" * 80)
        print(fills_report)
    
    print()
    print("=" * 80)
    print("Tips:")
    print("  - Adjust strategy parameters in the config to optimize performance")
    print("  - Try different EMA periods or MACD settings")
    print("  - Experiment with different stop loss and take profit levels")
    print("  - Use different timeframes (5min, 30min, 1H) by changing freq parameter")
    print("=" * 80)
    print()


if __name__ == "__main__":
    try:
        run_backtest_with_real_data()
    except Exception as e:
        print(f"\n❌ Error occurred: {e}")
        import traceback
        traceback.print_exc()

