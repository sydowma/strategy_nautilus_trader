"""
Main entry point for running backtests and live trading with Strategy1.

This script demonstrates how to set up and run a backtest using NautilusTrader
with the Strategy1 (EMA + MACD + Pivot Points) strategy.
"""

from decimal import Decimal
from nautilus_trader.backtest.engine import BacktestEngine, BacktestEngineConfig
from nautilus_trader.backtest.node import BacktestNode, BacktestDataConfig, BacktestRunConfig
from nautilus_trader.model.identifiers import Venue
from nautilus_trader.persistence.catalog import ParquetDataCatalog
from nautilus_trader.test_kit.providers import TestInstrumentProvider

from bot.bot1 import Strategy1, Strategy1Config


def run_backtest_example():
    """
    Run a simple backtest example using Strategy1.
    
    This is a demonstration of how to set up and run a backtest.
    In production, you would:
    1. Load historical data from a data catalog or CSV
    2. Configure proper risk management parameters
    3. Run comprehensive backtests with different parameters
    4. Analyze results and optimize the strategy
    """
    
    print("=" * 80)
    print("NautilusTrader - Strategy1 Backtest Example")
    print("=" * 80)
    print()
    print("Strategy Components:")
    print("  - EMA (20, 50, 100, 200) for trend identification")
    print("  - MACD (12, 26, 9) for momentum signals")
    print("  - Camarilla Pivot Points for support/resistance")
    print()
    print("Trading Rules:")
    print("  - LONG: Uptrend + MACD bullish crossover + price near support")
    print("  - SHORT: Downtrend + MACD bearish crossover + price near resistance")
    print("  - Stop Loss: -2% | Take Profit: +4% (2:1 R/R)")
    print()
    print("=" * 80)
    print()
    
    # Note: This is a simplified example
    # In production, you would need to:
    # 1. Set up a proper data catalog with historical data
    # 2. Configure the backtest engine with appropriate venues and instruments
    # 3. Load actual market data (bars, quotes, trades, etc.)
    
    print("To run a full backtest, you need to:")
    print()
    print("1. Prepare historical data:")
    print("   - Download historical OHLCV data for your instrument")
    print("   - Convert to Parquet format using NautilusTrader's data catalog")
    print()
    print("2. Set up data catalog:")
    print("   ```python")
    print("   from nautilus_trader.persistence.catalog import ParquetDataCatalog")
    print("   catalog = ParquetDataCatalog('./catalog')")
    print("   # Load your data into the catalog")
    print("   ```")
    print()
    print("3. Configure backtest:")
    print("   ```python")
    print("   # Create strategy config")
    print("   config = Strategy1Config(")
    print("       instrument_id='BTCUSDT-PERP.BINANCE',")
    print("       bar_type='BTCUSDT-PERP.BINANCE-15-MINUTE-LAST-EXTERNAL',")
    print("       ema_periods=[20, 50, 100, 200],")
    print("       macd_fast_period=12,")
    print("       macd_slow_period=26,")
    print("       macd_signal_period=9,")
    print("       risk_percent=0.01,")
    print("   )")
    print()
    print("   # Create backtest node")
    print("   node = BacktestNode()")
    print()
    print("   # Add venue and instruments")
    print("   node.add_venue(")
    print("       venue=Venue('BINANCE'),")
    print("       oms_type=OmsType.NETTING,")
    print("       account_type=AccountType.MARGIN,")
    print("       base_currency=USD,")
    print("       starting_balances=[Money(100000, USD)],")
    print("   )")
    print()
    print("   # Add data")
    print("   node.add_data(")
    print("       data=bars,  # Your historical bar data")
    print("       client_id=ClientId('BINANCE'),")
    print("   )")
    print()
    print("   # Add strategy")
    print("   node.add_strategy(Strategy1, config)")
    print()
    print("   # Run backtest")
    print("   result = node.run()")
    print("   ```")
    print()
    print("4. Analyze results:")
    print("   ```python")
    print("   # Get performance stats")
    print("   stats = result.stats_returns()")
    print("   print(stats)")
    print()
    print("   # Generate performance report")
    print("   report = result.stats_pnls()")
    print("   print(report)")
    print("   ```")
    print()
    print("=" * 80)
    print()
    print("Example Strategy Configuration:")
    print()
    
    # Create example configuration
    config = Strategy1Config(
        instrument_id="BTCUSDT-PERP.BINANCE",
        bar_type="BTCUSDT-PERP.BINANCE-15-MINUTE-LAST-EXTERNAL",
        ema_periods=[20, 50, 100, 200],
        macd_fast_period=13,
        macd_slow_period=34,
        macd_signal_period=9,
        risk_percent=0.01,
        stop_loss_atr_multiplier=2.0,
        take_profit_risk_reward=2.0,
    )
    
    print(f"  Instrument: {config.instrument_id}")
    print(f"  Bar Type: {config.bar_type}")
    print(f"  EMA Periods: {config.ema_periods}")
    print(f"  MACD: {config.macd_fast_period}/{config.macd_slow_period}/{config.macd_signal_period}")
    print(f"  Risk per trade: {config.risk_percent * 100}%")
    print(f"  Stop Loss: {config.stop_loss_atr_multiplier}x ATR")
    print(f"  Take Profit R/R: {config.take_profit_risk_reward}:1")
    print()
    print("=" * 80)
    print()
    print("For more information about NautilusTrader backtesting, visit:")
    print("https://nautilustrader.io/docs/latest/concepts/backtesting")
    print()


def main():
    """Main entry point."""
    try:
        run_backtest_example()
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
