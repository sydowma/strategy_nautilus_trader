"""
从 Binance 下载加密货币历史数据

此脚本使用 ccxt 库直接从 Binance 下载历史K线数据，
并保存为 CSV 格式，方便后续回测使用。

支持：
- 现货交易对
- 合约交易对
- 多种时间周期
- 自定义时间范围
"""

import ccxt
import pandas as pd
from datetime import datetime, timedelta
import time
import os


def download_binance_data(
    symbol: str = 'BTC/USDT',
    timeframe: str = '15m',
    since_days_ago: int = 30,
    output_dir: str = '../data',
    exchange_type: str = 'spot'
):
    """
    从 Binance 下载历史数据
    
    Parameters
    ----------
    symbol : str
        交易对符号，例如 'BTC/USDT', 'ETH/USDT'
    timeframe : str
        时间周期：'1m', '5m', '15m', '30m', '1h', '4h', '1d'
    since_days_ago : int
        下载多少天前的数据
    output_dir : str
        输出目录
    exchange_type : str
        交易所类型：'spot' (现货) 或 'future' (合约)
    """
    
    print("=" * 80)
    print("Binance 数据下载工具")
    print("=" * 80)
    print()
    
    # 创建交易所实例
    if exchange_type == 'spot':
        exchange = ccxt.binance({
            'enableRateLimit': True,
            'options': {'defaultType': 'spot'}
        })
        print(f"📊 交易类型：现货")
    else:
        exchange = ccxt.binance({
            'enableRateLimit': True,
            'options': {'defaultType': 'future'}
        })
        print(f"📊 交易类型：合约")
    
    print(f"💱 交易对：{symbol}")
    print(f"⏰ 时间周期：{timeframe}")
    print(f"📅 数据范围：最近 {since_days_ago} 天")
    print()
    
    # 计算起始时间
    since = exchange.parse8601(
        (datetime.now() - timedelta(days=since_days_ago)).strftime('%Y-%m-%dT%H:%M:%SZ')
    )
    
    all_ohlcv = []
    limit = 1000  # Binance 每次请求最多返回 1000 条
    
    print("⬇️ 开始下载数据...")
    
    while True:
        try:
            print(f"  正在获取数据，起始时间：{datetime.fromtimestamp(since/1000).strftime('%Y-%m-%d %H:%M:%S')}", end='')
            
            ohlcv = exchange.fetch_ohlcv(
                symbol=symbol,
                timeframe=timeframe,
                since=since,
                limit=limit
            )
            
            if not ohlcv:
                print(" - 无更多数据")
                break
            
            print(f" - 获取 {len(ohlcv)} 条")
            
            all_ohlcv.extend(ohlcv)
            
            # 更新起始时间为最后一条数据的时间
            since = ohlcv[-1][0] + 1
            
            # 如果返回的数据少于limit，说明已经到最新了
            if len(ohlcv) < limit:
                break
            
            # 限制请求频率，避免被限制
            time.sleep(exchange.rateLimit / 1000)
            
        except Exception as e:
            print(f"\n❌ 下载出错：{e}")
            break
    
    if not all_ohlcv:
        print("\n❌ 未能下载到任何数据")
        return None
    
    print(f"\n✅ 总共下载 {len(all_ohlcv)} 条数据")
    print()
    
    # 转换为 DataFrame
    df = pd.DataFrame(
        all_ohlcv,
        columns=['timestamp', 'open', 'high', 'low', 'close', 'volume']
    )
    
    # 转换时间戳为日期时间
    df['datetime'] = pd.to_datetime(df['timestamp'], unit='ms')
    
    # 重新排列列
    df = df[['datetime', 'timestamp', 'open', 'high', 'low', 'close', 'volume']]
    
    # 显示数据摘要
    print("📊 数据摘要：")
    print("-" * 80)
    print(f"  时间范围：{df['datetime'].min()} 至 {df['datetime'].max()}")
    print(f"  数据条数：{len(df)}")
    print(f"  价格范围：${df['low'].min():.2f} - ${df['high'].max():.2f}")
    print()
    
    # 显示前几行
    print("前5行数据：")
    print(df.head())
    print()
    
    # 保存到文件
    os.makedirs(output_dir, exist_ok=True)
    
    # 生成文件名
    symbol_clean = symbol.replace('/', '').lower()
    filename = f"{symbol_clean}_{timeframe}_{since_days_ago}days.csv"
    filepath = os.path.join(output_dir, filename)
    
    df.to_csv(filepath, index=False)
    
    print(f"💾 数据已保存到：{filepath}")
    print()
    
    return df


def download_multiple_pairs():
    """下载多个交易对的数据"""
    
    pairs = [
        ('BTC/USDT', '15m', 30),
        ('ETH/USDT', '15m', 30),
        ('BNB/USDT', '15m', 30),
    ]
    
    print("=" * 80)
    print("批量下载多个交易对数据")
    print("=" * 80)
    print()
    
    for symbol, timeframe, days in pairs:
        print(f"\n开始下载 {symbol}...")
        download_binance_data(
            symbol=symbol,
            timeframe=timeframe,
            since_days_ago=days,
            output_dir='../data/binance'
        )
        time.sleep(2)  # 避免请求过快
    
    print("\n" + "=" * 80)
    print("✅ 所有数据下载完成！")
    print("=" * 80)


def main():
    """主函数"""
    print()
    print("选择下载模式：")
    print("1. 下载单个交易对")
    print("2. 批量下载多个交易对（BTC/ETH/BNB）")
    print("3. 自定义下载")
    print()
    
    choice = input("请选择 (1/2/3) [默认=1]: ").strip() or "1"
    
    if choice == "1":
        # 默认下载 BTCUSDT 15分钟数据，最近30天
        download_binance_data(
            symbol='BTC/USDT',
            timeframe='15m',
            since_days_ago=30,
            output_dir='../data/binance',
            exchange_type='spot'
        )
    
    elif choice == "2":
        download_multiple_pairs()
    
    elif choice == "3":
        print("\n请输入以下参数：")
        symbol = input("交易对 (如 BTC/USDT) [默认=BTC/USDT]: ").strip() or "BTC/USDT"
        timeframe = input("时间周期 (如 15m, 1h, 4h) [默认=15m]: ").strip() or "15m"
        days = int(input("下载天数 [默认=30]: ").strip() or "30")
        exchange_type = input("交易类型 (spot/future) [默认=spot]: ").strip() or "spot"
        
        download_binance_data(
            symbol=symbol,
            timeframe=timeframe,
            since_days_ago=days,
            output_dir='../data/binance',
            exchange_type=exchange_type
        )
    
    print()
    print("💡 提示：")
    print("  - 下载的数据保存在 data/binance/ 目录下")
    print("  - 可以使用这些数据进行回测")
    print("  - 建议定期更新数据以保持最新")
    print()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️ 下载已取消")
    except Exception as e:
        print(f"\n❌ 发生错误：{e}")
        import traceback
        traceback.print_exc()

