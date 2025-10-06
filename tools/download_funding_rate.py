"""
Download Funding Rate Data from Binance

This script downloads historical funding rate data for perpetual futures
from Binance and saves it to CSV format.
"""

import os
import pandas as pd
import ccxt
from datetime import datetime, timedelta


def download_funding_rate_data(
    symbol: str = 'BTC/USDT',
    since_days_ago: int = 30,
    output_dir: str = '../data/funding_rates'
):
    """
    Download funding rate data from Binance
    
    Parameters
    ----------
    symbol : str
        Trading pair symbol (e.g., 'BTC/USDT')
    since_days_ago : int
        Number of days of historical data to download
    output_dir : str
        Output directory for CSV files
        
    Returns
    -------
    str
        Path to the saved CSV file
    """
    print("=" * 80)
    print("📥 Downloading Funding Rate Data from Binance")
    print("=" * 80)
    print()
    
    # Initialize exchange
    exchange = ccxt.binance({
        'enableRateLimit': True,
        'options': {
            'defaultType': 'future',  # Use futures market
        }
    })
    
    # Calculate time range
    end_time = datetime.utcnow()
    start_time = end_time - timedelta(days=since_days_ago)
    
    # Convert to milliseconds
    since_ms = int(start_time.timestamp() * 1000)
    
    print(f"Symbol: {symbol}")
    print(f"Date range: {start_time.strftime('%Y-%m-%d')} to {end_time.strftime('%Y-%m-%d')}")
    print(f"Days: {since_days_ago}")
    print()
    
    # Fetch funding rate history
    print("Fetching funding rate data...")
    
    try:
        # Binance funding rate history
        # Note: Binance returns funding rates in 8-hour intervals
        funding_rates = []
        
        # Create market symbol for futures
        market_symbol = symbol.replace('/', '')
        
        # Fetch data
        all_rates = exchange.fapipublic_get_fundingrate({
            'symbol': market_symbol,
            'startTime': since_ms,
            'limit': 1000  # Max records per request
        })
        
        print(f"✅ Fetched {len(all_rates)} funding rate records")
        print()
        
        # Process data
        for rate in all_rates:
            funding_rates.append({
                'timestamp': int(rate['fundingTime']),
                'datetime': datetime.fromtimestamp(int(rate['fundingTime']) / 1000).strftime('%Y-%m-%d %H:%M:%S'),
                'symbol': rate['symbol'],
                'funding_rate': float(rate['fundingRate']),
            })
        
        # Create DataFrame
        df = pd.DataFrame(funding_rates)
        
        # Sort by timestamp
        df = df.sort_values('timestamp')
        
        # Statistics
        print("📊 Funding Rate Statistics:")
        print(f"   Records: {len(df)}")
        print(f"   Date range: {df['datetime'].min()} to {df['datetime'].max()}")
        print(f"   Avg rate: {df['funding_rate'].mean():.6f} ({df['funding_rate'].mean()*100:.4f}%)")
        print(f"   Min rate: {df['funding_rate'].min():.6f} ({df['funding_rate'].min()*100:.4f}%)")
        print(f"   Max rate: {df['funding_rate'].max():.6f} ({df['funding_rate'].max()*100:.4f}%)")
        print(f"   Std dev:  {df['funding_rate'].std():.6f}")
        print()
        
        # Save to CSV
        os.makedirs(output_dir, exist_ok=True)
        
        filename = f"{symbol.replace('/', '').lower()}_funding_rate_{since_days_ago}days.csv"
        output_file = os.path.join(output_dir, filename)
        
        df.to_csv(output_file, index=False)
        
        print(f"💾 Data saved to: {output_file}")
        print()
        
        # Show sample
        print("Sample data (first 5 records):")
        print(df.head())
        print()
        
        print("=" * 80)
        print("✅ Download complete!")
        print("=" * 80)
        
        return output_file
        
    except Exception as e:
        print(f"❌ Error downloading data: {e}")
        import traceback
        traceback.print_exc()
        return None


def main():
    """
    Main function
    """
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Download funding rate data from Binance'
    )
    parser.add_argument(
        '--symbol',
        type=str,
        default='BTC/USDT',
        help='Trading pair symbol (default: BTC/USDT)'
    )
    parser.add_argument(
        '--days',
        type=int,
        default=30,
        help='Number of days of historical data (default: 30)'
    )
    parser.add_argument(
        '--output',
        type=str,
        default='../data/funding_rates',
        help='Output directory (default: ../data/funding_rates)'
    )
    
    args = parser.parse_args()
    
    download_funding_rate_data(
        symbol=args.symbol,
        since_days_ago=args.days,
        output_dir=args.output
    )


if __name__ == '__main__':
    main()

