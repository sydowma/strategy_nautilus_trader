"""
Load CSV tick data and convert to bars for backtesting.

This script processes the EURUSD tick data from CSV format and
converts it into bar data suitable for NautilusTrader backtesting.
"""

import gzip
import pandas as pd
from datetime import datetime, timezone
from decimal import Decimal

from nautilus_trader.core.datetime import dt_to_unix_nanos
from nautilus_trader.model.data import Bar, BarType
from nautilus_trader.model.enums import AggregationSource, BarAggregation, PriceType
from nautilus_trader.model.identifiers import InstrumentId, Symbol, Venue
from nautilus_trader.model.instruments import CurrencyPair
from nautilus_trader.model.currencies import EUR, USD
from nautilus_trader.model.objects import Price, Quantity


def load_tick_data_from_csv(filepath: str) -> pd.DataFrame:
    """
    Load tick data from compressed CSV file.
    
    Parameters
    ----------
    filepath : str
        Path to the CSV.gz file
        
    Returns
    -------
    pd.DataFrame
        DataFrame with columns: timestamp, bid, ask, volume
    """
    print(f"Loading data from {filepath}...")
    
    # Read compressed CSV
    with gzip.open(filepath, 'rt') as f:
        df = pd.read_csv(
            f,
            header=None,
            names=['timestamp', 'bid', 'ask', 'volume']
        )
    
    # Parse timestamp
    df['timestamp'] = pd.to_datetime(
        df['timestamp'].astype(str),
        format='%Y%m%d %H%M%S%f'
    )
    
    # Set timezone to UTC
    df['timestamp'] = df['timestamp'].dt.tz_localize('UTC')
    
    print(f"Loaded {len(df)} ticks")
    print(f"Date range: {df['timestamp'].min()} to {df['timestamp'].max()}")
    print(f"Price range: {df['bid'].min():.5f} to {df['ask'].max():.5f}")
    
    return df


def convert_ticks_to_bars(
    df: pd.DataFrame,
    instrument_id: InstrumentId,
    bar_type: BarType,
    freq: str = '15min'
) -> list[Bar]:
    """
    Convert tick data to OHLC bars.
    
    Parameters
    ----------
    df : pd.DataFrame
        Tick data with timestamp, bid, ask columns
    instrument_id : InstrumentId
        Instrument identifier
    bar_type : BarType
        Bar type specification
    freq : str
        Pandas frequency string (e.g., '15min', '1H', '5min')
        
    Returns
    -------
    list[Bar]
        List of bars
    """
    print(f"Converting ticks to {freq} bars...")
    
    # Calculate mid price
    df['mid'] = (df['bid'] + df['ask']) / 2
    
    # Set timestamp as index
    df = df.set_index('timestamp')
    
    # Resample to bars using mid price
    ohlc = df['mid'].resample(freq).ohlc()
    volume = df['volume'].resample(freq).sum()
    
    # Remove NaN rows
    ohlc = ohlc.dropna()
    
    print(f"Created {len(ohlc)} bars")
    
    # Convert to Bar objects
    bars = []
    for timestamp, row in ohlc.iterrows():
        ts_init = dt_to_unix_nanos(timestamp.to_pydatetime())
        
        bar = Bar(
            bar_type=bar_type,
            open=Price.from_str(f"{row['open']:.5f}"),
            high=Price.from_str(f"{row['high']:.5f}"),
            low=Price.from_str(f"{row['low']:.5f}"),
            close=Price.from_str(f"{row['close']:.5f}"),
            volume=Quantity.from_int(int(volume.loc[timestamp]) if volume.loc[timestamp] > 0 else 1),
            ts_event=ts_init,
            ts_init=ts_init,
        )
        bars.append(bar)
    
    return bars


def create_eurusd_instrument() -> CurrencyPair:
    """
    Create EURUSD currency pair instrument.
    
    Returns
    -------
    CurrencyPair
        EURUSD instrument
    """
    venue = Venue("SIM")
    symbol = Symbol("EUR/USD")
    instrument_id = InstrumentId(symbol=symbol, venue=venue)
    
    instrument = CurrencyPair(
        id=instrument_id,
        raw_symbol=symbol,
        base_currency=EUR,
        quote_currency=USD,
        price_precision=5,
        size_precision=0,
        price_increment=Price.from_str("0.00001"),
        size_increment=Quantity.from_int(1),
        lot_size=Quantity.from_int(1000),
        max_quantity=Quantity.from_int(1_000_000),
        min_quantity=Quantity.from_int(1),
        max_price=Price.from_str("9.99999"),
        min_price=Price.from_str("0.00001"),
        margin_init=Decimal("0.03"),
        margin_maint=Decimal("0.03"),
        maker_fee=Decimal("0.00002"),
        taker_fee=Decimal("0.00002"),
        ts_event=0,
        ts_init=0,
    )
    
    return instrument


def main():
    """
    Main function to demonstrate data loading.
    """
    # File path
    csv_file = "/Users/oker/GitHub/bot/strategy_nautilus_trader/DAT_ASCII_EURUSD_T_202001.csv.gz"
    
    # Load tick data
    df = load_tick_data_from_csv(csv_file)
    
    # Create instrument
    instrument = create_eurusd_instrument()
    
    # Define bar type
    bar_type = BarType(
        instrument_id=instrument.id,
        bar_spec=BarType.parse("15-MINUTE-MID"),
        aggregation_source=AggregationSource.EXTERNAL,
    )
    
    # Convert to bars
    bars = convert_ticks_to_bars(df, instrument.id, bar_type, freq='15min')
    
    print("\n" + "=" * 80)
    print("Data processing complete!")
    print(f"Instrument: {instrument.id}")
    print(f"Total bars: {len(bars)}")
    print(f"First bar: {bars[0].ts_init.as_datetime()} - OHLC: {bars[0].open}/{bars[0].high}/{bars[0].low}/{bars[0].close}")
    print(f"Last bar: {bars[-1].ts_init.as_datetime()} - OHLC: {bars[-1].open}/{bars[-1].high}/{bars[-1].low}/{bars[-1].close}")
    print("=" * 80)
    
    return instrument, bars


if __name__ == "__main__":
    main()

