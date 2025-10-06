"""
Funding Rate Arbitrage Backtest Example

This script demonstrates how to backtest a funding rate arbitrage strategy
that profits from collecting funding payments by maintaining a market-neutral
position (long spot + short futures).
"""

import sys
import os
import pandas as pd
from decimal import Decimal
from datetime import datetime, timedelta

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set pandas display options
pd.set_option('display.max_rows', None)
pd.set_option('display.max_columns', None)
pd.set_option('display.width', None)
pd.set_option('display.max_colwidth', None)

from nautilus_trader.backtest.engine import BacktestEngine, BacktestEngineConfig
from nautilus_trader.model.currencies import BTC, USDT
from nautilus_trader.model.data import Bar, BarType, BarSpecification
from nautilus_trader.model.enums import (
    AccountType,
    AggregationSource,
    BarAggregation,
    OmsType,
    PriceType,
)
from nautilus_trader.model.identifiers import InstrumentId, Symbol, Venue
from nautilus_trader.model.instruments import CryptoPerpetual
from nautilus_trader.model.objects import Money, Price, Quantity
from nautilus_trader.core.datetime import dt_to_unix_nanos
from nautilus_trader.config import LoggingConfig

from bot.funding_arbitrage_strategy import FundingArbitrageStrategy, FundingArbitrageConfig
from tools.funding_rate_simulator import FundingRateData, generate_synthetic_funding_rates


def load_csv_data(csv_file: str) -> pd.DataFrame:
    """Load CSV data file"""
    print(f"📂 Loading price data: {csv_file}")
    
    df = pd.read_csv(csv_file)
    
    if 'datetime' in df.columns:
        df['datetime'] = pd.to_datetime(df['datetime'])
    elif 'timestamp' in df.columns:
        df['datetime'] = pd.to_datetime(df['timestamp'], unit='ms')
    
    print(f"✅ Loaded {len(df)} bars")
    print(f"   Date range: {df['datetime'].min()} to {df['datetime'].max()}")
    print()
    
    return df


def convert_to_nautilus_bars(
    df: pd.DataFrame,
    instrument_id: InstrumentId,
    bar_type: BarType
) -> list[Bar]:
    """Convert DataFrame to Nautilus Bar objects"""
    print("🔄 Converting to Nautilus bars...")
    
    bars = []
    for _, row in df.iterrows():
        ts_init = dt_to_unix_nanos(row['datetime'].to_pydatetime())
        
        bar = Bar(
            bar_type=bar_type,
            open=Price.from_str(f"{row['open']:.8f}"),
            high=Price.from_str(f"{row['high']:.8f}"),
            low=Price.from_str(f"{row['low']:.8f}"),
            close=Price.from_str(f"{row['close']:.8f}"),
            volume=Quantity.from_str(f"{row['volume']:.8f}"),
            ts_event=ts_init,
            ts_init=ts_init,
        )
        bars.append(bar)
    
    print(f"✅ Converted {len(bars)} bars")
    print()
    
    return bars


def create_perpetual_instrument(
    symbol: str = 'BTCUSDT',
    venue_name: str = 'BINANCE'
) -> CryptoPerpetual:
    """Create perpetual futures instrument"""
    venue = Venue(venue_name)
    instrument_symbol = Symbol(f"{symbol}-PERP")
    instrument_id = InstrumentId(symbol=instrument_symbol, venue=venue)
    
    instrument = CryptoPerpetual(
        instrument_id=instrument_id,
        raw_symbol=instrument_symbol,
        base_currency=BTC,
        quote_currency=USDT,
        settlement_currency=USDT,
        is_inverse=False,
        price_precision=8,
        size_precision=8,
        price_increment=Price.from_str("0.00000001"),
        size_increment=Quantity.from_str("0.00000001"),
        max_quantity=Quantity.from_str("1000.0"),
        min_quantity=Quantity.from_str("0.00000001"),
        max_price=Price.from_str("1000000.0"),
        min_price=Price.from_str("0.00000001"),
        margin_init=Decimal("0.1"),
        margin_maint=Decimal("0.05"),
        maker_fee=Decimal("0.0002"),
        taker_fee=Decimal("0.0004"),
        ts_event=0,
        ts_init=0,
    )
    
    return instrument


def run_funding_arbitrage_backtest(
    price_csv_file: str,
    funding_csv_file: str = None,
    symbol: str = 'BTCUSDT',
    timeframe: str = '1h'
):
    """
    Run funding rate arbitrage backtest
    
    Parameters
    ----------
    price_csv_file : str
        CSV file with price data
    funding_csv_file : str, optional
        CSV file with funding rate data (if None, synthetic data is used)
    symbol : str
        Trading symbol
    timeframe : str
        Timeframe
    """
    print("=" * 80)
    print("💰 FUNDING RATE ARBITRAGE BACKTEST")
    print("=" * 80)
    print()
    
    # Load price data
    df = load_csv_data(price_csv_file)
    
    # Create instruments (both spot and perpetual)
    # Create perpetual (futures) instrument
    futures_instrument = create_perpetual_instrument(symbol=symbol, venue_name='BINANCE')
    venue = futures_instrument.id.venue
    
    # Create spot instrument with same base
    from nautilus_trader.model.instruments import CryptoPerpetual, CryptoFuture, CurrencyPair
    from nautilus_trader.model.identifiers import InstrumentId, Symbol, Venue
    from nautilus_trader.model.currencies import BTC, USDT
    from nautilus_trader.model.objects import Price, Quantity, Money
    from decimal import Decimal
    
    spot_instrument_id = InstrumentId(
        symbol=Symbol(symbol),
        venue=venue
    )
    
    spot_instrument = CurrencyPair(
        instrument_id=spot_instrument_id,
        raw_symbol=Symbol(symbol),
        base_currency=BTC,
        quote_currency=USDT,
        price_precision=8,
        size_precision=8,
        price_increment=Price.from_str("0.00000001"),
        size_increment=Quantity.from_str("0.00000001"),
        lot_size=None,
        max_quantity=Quantity.from_str("1000.0"),
        min_quantity=Quantity.from_str("0.00000001"),
        max_price=Price.from_str("1000000.0"),
        min_price=Price.from_str("0.00000001"),
        margin_init=Decimal("0.1"),
        margin_maint=Decimal("0.05"),
        maker_fee=Decimal("0.0002"),
        taker_fee=Decimal("0.0004"),
        ts_event=0,
        ts_init=0,
    )
    
    print(f"📊 Configuration:")
    print(f"   Spot: {spot_instrument.id}")
    print(f"   Futures: {futures_instrument.id}")
    print(f"   Timeframe: {timeframe}")
    print()
    
    # Define bar type
    timeframe_mapping = {
        '15m': (15, BarAggregation.MINUTE),
        '30m': (30, BarAggregation.MINUTE),
        '1h': (1, BarAggregation.HOUR),
        '4h': (4, BarAggregation.HOUR),
        '8h': (8, BarAggregation.HOUR),
    }
    
    step, aggregation = timeframe_mapping.get(timeframe.lower(), (1, BarAggregation.HOUR))
    
    bar_spec = BarSpecification(
        step=step,
        aggregation=aggregation,
        price_type=PriceType.LAST,
    )
    
    # Create bar types for both instruments
    futures_bar_type = BarType(
        instrument_id=futures_instrument.id,
        bar_spec=bar_spec,
        aggregation_source=AggregationSource.EXTERNAL,
    )
    
    spot_bar_type = BarType(
        instrument_id=spot_instrument.id,
        bar_spec=bar_spec,
        aggregation_source=AggregationSource.EXTERNAL,
    )
    
    # Convert data (use same price data for both spot and futures)
    futures_bars = convert_to_nautilus_bars(df, futures_instrument.id, futures_bar_type)
    spot_bars = convert_to_nautilus_bars(df, spot_instrument.id, spot_bar_type)
    
    # Load or generate funding rate data
    print("📈 Loading funding rate data...")
    
    if funding_csv_file and os.path.exists(funding_csv_file):
        # Load real funding rate data
        funding_data = FundingRateData()
        funding_data.load_from_csv(funding_csv_file)
    else:
        # Generate synthetic funding rate data
        print("⚠️  No funding rate file provided, generating synthetic data")
        start_date = df['datetime'].min()
        end_date = df['datetime'].max()
        funding_data = generate_synthetic_funding_rates(
            start_date=start_date.to_pydatetime(),
            end_date=end_date.to_pydatetime(),
            base_rate=0.0001,  # 0.01% per 8h (typical positive rate)
            volatility=0.00005
        )
        print(f"✅ Generated {len(funding_data.rates)} synthetic funding rates")
    
    print()
    
    # Create backtest engine
    print("⚙️  Configuring backtest engine...")
    config = BacktestEngineConfig(
        logging=LoggingConfig(log_level="INFO"),
    )
    
    engine = BacktestEngine(config=config)
    
    # Add venue
    engine.add_venue(
        venue=venue,
        oms_type=OmsType.NETTING,
        account_type=AccountType.MARGIN,
        base_currency=USDT,
        starting_balances=[Money(100000, USDT)],
    )
    
    # Add instruments and data
    engine.add_instrument(futures_instrument)
    engine.add_instrument(spot_instrument)
    engine.add_data(futures_bars)
    engine.add_data(spot_bars)
    
    print(f"   Initial balance: $10,000 USDT")
    print()
    
    # Configure strategy
    print("🎯 Configuring strategy...")
    venue_name = venue.value  # Get venue name string from venue object
    strategy_config = FundingArbitrageConfig(
        spot_instrument_id=str(spot_instrument.id),
        futures_instrument_id=str(futures_instrument.id),
        bar_type=str(futures_bar_type),
        funding_rate_threshold=0.0000005,  # 0.00005% - enter when rate is positive
        exit_funding_rate=-0.001,  # -0.1% - exit if rate drops too low  
        position_size_usdt=50000.0,  # $5,000 position size
        max_position_duration_hours=16800,  # Max 700 days per position (1 week)
    )
    
    print(f"   Funding threshold: {strategy_config.funding_rate_threshold*100:.3f}%")
    print(f"   Exit rate: {strategy_config.exit_funding_rate*100:.3f}%")
    print(f"   Position size: ${strategy_config.position_size_usdt:,.0f}")
    print(f"   Max duration: {strategy_config.max_position_duration_hours}h")
    print()
    
    # Create and add strategy
    strategy = FundingArbitrageStrategy(config=strategy_config)
    strategy.set_funding_data(funding_data)
    engine.add_strategy(strategy)
    
    # Run backtest
    print("=" * 80)
    print("🚀 Running backtest...")
    print("=" * 80)
    print()
    
    engine.run()
    
    print()
    print("=" * 80)
    print("✅ Backtest complete!")
    print("=" * 80)
    print()
    
    # Display results
    print("📊 RESULTS:")
    print("=" * 80)
    
    # Strategy performance
    performance = strategy.get_performance_summary()
    
    print(f"\n💼 Strategy Performance:")
    print(f"   Total arbitrage cycles: {performance['total_trades']}")
    print(f"   Funding settlements: {performance['total_settlements']}")
    print(f"   Total funding received: ${performance['total_received']:,.2f}")
    print(f"   Total funding paid: ${performance['total_paid']:,.2f}")
    print(f"   Net funding profit: ${performance['net_funding']:,.2f}")
    print(f"   Avg funding rate: {performance['avg_funding_rate']:.6f} ({performance['avg_funding_rate']*100:.4f}%)")
    
    # Account report
    account_report = engine.trader.generate_account_report(venue)
    print(f"\n💰 Account Report:")
    print("-" * 80)
    print(account_report)
    
    print()
    print("=" * 80)


def main():
    """Main function"""
    
    # Check for data files
    data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'binance')
    funding_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'funding_rates')
    
    if os.path.exists(data_dir):
        csv_files = [f for f in os.listdir(data_dir) if f.endswith('.csv')]
        
        if csv_files:
            print("\n📁 Available price data files:")
            for i, f in enumerate(csv_files, 1):
                print(f"  {i}. {f}")
            
            print()
            choice = input(f"Select file (1-{len(csv_files)}) [default=1]: ").strip() or "1"
            
            try:
                idx = int(choice) - 1
                if 0 <= idx < len(csv_files):
                    price_file = os.path.join(data_dir, csv_files[idx])
                    
                    # Parse symbol from filename
                    filename = csv_files[idx]
                    parts = filename.replace('.csv', '').split('_')
                    symbol = parts[0].upper() if parts else 'BTCUSDT'
                    
                    # Check for funding rate file
                    funding_file = None
                    if os.path.exists(funding_dir):
                        funding_files = [f for f in os.listdir(funding_dir) 
                                       if f.startswith(symbol.lower()) and f.endswith('.csv')]
                        if funding_files:
                            funding_file = os.path.join(funding_dir, funding_files[0])
                            print(f"✅ Found funding rate data: {funding_files[0]}")
                    
                    run_funding_arbitrage_backtest(
                        price_csv_file=price_file,
                        funding_csv_file=funding_file,
                        symbol=symbol,
                        timeframe='1h'
                    )
                else:
                    print("❌ Invalid selection")
            except (ValueError, IndexError) as e:
                print(f"❌ Invalid input: {e}")
        else:
            print("\n❌ No price data files found")
            print("\n💡 Please run: python tools/download_binance_data.py")
    else:
        print("\n❌ Data directory not found")
        print("\n💡 Please run: python tools/download_binance_data.py")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

