"""
使用 Binance 历史数据进行加密货币回测

此脚本演示如何使用 NautilusTrader 的数据加载器直接从 Binance 获取历史数据
并进行回测，无需手动准备数据文件。

支持的交易所：
- Binance (现货和合约)
- Binance US
- OKX
- Bybit
等等...
"""

import sys
import os
from datetime import datetime, timedelta
from decimal import Decimal

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from nautilus_trader.backtest.engine import BacktestEngine, BacktestEngineConfig
from nautilus_trader.backtest.node import BacktestDataConfig, BacktestNode, BacktestRunConfig
from nautilus_trader.common.enums import LogLevel
from nautilus_trader.model.currencies import USD, USDT
from nautilus_trader.model.enums import AccountType, OmsType
from nautilus_trader.model.identifiers import Venue
from nautilus_trader.model.objects import Money
from nautilus_trader.persistence.catalog import ParquetDataCatalog
from nautilus_trader.persistence.wranglers import BarDataWrangler
from nautilus_trader.test_kit.providers import TestDataProvider, TestInstrumentProvider

from bot.bot1 import Strategy1, Strategy1Config


def run_crypto_backtest_with_sample_data():
    """
    使用示例数据运行加密货币回测
    
    注意：这是一个简化的示例，使用模拟数据。
    要使用真实的 Binance 历史数据，请参考下面的说明。
    """
    print("=" * 80)
    print("加密货币回测 - Strategy1")
    print("=" * 80)
    print()
    
    print("📝 说明：")
    print("  此示例使用 NautilusTrader 的测试数据演示回测流程")
    print("  要使用真实 Binance 数据，请按照下面的步骤操作：")
    print()
    
    # 创建回测节点
    node = BacktestNode()
    
    # 配置 Binance 模拟环境
    venue = Venue("BINANCE")
    
    # 添加交易所配置
    node.add_venue(
        venue=venue,
        oms_type=OmsType.NETTING,
        account_type=AccountType.MARGIN,
        base_currency=USDT,
        starting_balances=[Money(10000, USDT)],
    )
    
    # 创建加密货币工具 (BTCUSDT)
    instrument = TestInstrumentProvider.btcusdt_binance()
    node.add_instrument(instrument)
    
    print(f"✅ 已配置交易环境：")
    print(f"  交易所：{venue}")
    print(f"  交易对：{instrument.id}")
    print(f"  初始资金：10,000 USDT")
    print()
    
    # 获取测试数据
    print("📊 加载测试数据...")
    provider = TestDataProvider()
    
    # 加载测试 bar 数据 (15分钟K线)
    bars = provider.read_csv_bars("btcusdt-15min-external.csv")[:1000]  # 使用前1000根K线
    
    if not bars:
        print("❌ 未找到测试数据文件")
        print()
        print("💡 请使用以下方法之一获取真实数据：")
        print_data_acquisition_methods()
        return
    
    # 添加数据到回测引擎
    node.add_data(bars)
    
    print(f"  已加载 {len(bars)} 根K线")
    print(f"  时间范围：{bars[0].ts_init.as_datetime()} 到 {bars[-1].ts_init.as_datetime()}")
    print()
    
    # 配置策略
    print("⚙️ 配置交易策略...")
    config = Strategy1Config(
        instrument_id=str(instrument.id),
        bar_type="BTCUSDT.BINANCE-15-MINUTE-LAST-EXTERNAL",
        ema_periods=[20, 50, 100, 200],
        macd_fast_period=12,
        macd_slow_period=26,
        macd_signal_period=9,
        risk_percent=0.01,
    )
    
    print(f"  EMA 周期：{config.ema_periods}")
    print(f"  MACD：{config.macd_fast_period}/{config.macd_slow_period}/{config.macd_signal_period}")
    print()
    
    # 添加策略
    strategies = [Strategy1]
    configs = [config]
    
    # 配置并运行回测
    run_config = BacktestRunConfig(
        engine=BacktestEngineConfig(
            strategies=strategies,
            logging=LogLevel.INFO,
        ),
    )
    
    print("=" * 80)
    print("🚀 开始回测...")
    print("=" * 80)
    print()
    
    # 运行回测
    result = node.run(configs=[config])
    
    print()
    print("=" * 80)
    print("✅ 回测完成！")
    print("=" * 80)
    print()
    
    # 显示结果
    print("📊 性能摘要：")
    print("-" * 80)
    
    # 这里可以添加性能统计
    print("提示：在生产环境中，使用 result.stats_returns() 和 result.stats_pnls() 获取详细统计")
    print()


def print_data_acquisition_methods():
    """打印获取加密货币数据的方法"""
    print()
    print("=" * 80)
    print("📥 获取加密货币历史数据的方法")
    print("=" * 80)
    print()
    
    print("方法 1：使用 NautilusTrader 数据客户端（推荐）")
    print("-" * 80)
    print("NautilusTrader 可以直接从交易所下载历史数据：")
    print()
    print("```python")
    print("from nautilus_trader.adapters.binance.http.client import BinanceHttpClient")
    print("from nautilus_trader.adapters.binance.common.enums import BinanceAccountType")
    print()
    print("# 创建 Binance 客户端（无需 API Key 可下载历史数据）")
    print("client = BinanceHttpClient(")
    print("    clock=LiveClock(),")
    print("    account_type=BinanceAccountType.SPOT,  # 或 USDT_FUTURE")
    print(")")
    print()
    print("# 下载历史 K线数据")
    print("bars = client.request_binance_bars(")
    print("    symbol='BTCUSDT',")
    print("    interval='15m',  # 15分钟")
    print("    start_time=start_timestamp,")
    print("    end_time=end_timestamp,")
    print("    limit=1000")
    print(")")
    print("```")
    print()
    
    print("方法 2：使用 ccxt 库下载数据")
    print("-" * 80)
    print("```bash")
    print("pip install ccxt")
    print("```")
    print()
    print("```python")
    print("import ccxt")
    print("import pandas as pd")
    print()
    print("# 创建交易所实例")
    print("exchange = ccxt.binance()")
    print()
    print("# 下载历史数据")
    print("ohlcv = exchange.fetch_ohlcv(")
    print("    symbol='BTC/USDT',")
    print("    timeframe='15m',")
    print("    limit=1000")
    print(")")
    print()
    print("# 转换为 DataFrame")
    print("df = pd.DataFrame(")
    print("    ohlcv,")
    print("    columns=['timestamp', 'open', 'high', 'low', 'close', 'volume']")
    print(")")
    print("```")
    print()
    
    print("方法 3：从币安官网下载历史数据")
    print("-" * 80)
    print("1. 访问：https://www.binance.com/zh-CN/landing/data")
    print("2. 选择数据类型：")
    print("   - 现货历史数据")
    print("   - 合约历史数据")
    print("3. 选择交易对和时间范围")
    print("4. 下载 CSV 文件")
    print()
    
    print("方法 4：使用我提供的数据下载脚本")
    print("-" * 80)
    print("运行以下命令创建数据下载脚本：")
    print("```bash")
    print("python examples/download_crypto_data.py")
    print("```")
    print()
    
    print("=" * 80)
    print()


if __name__ == "__main__":
    try:
        run_crypto_backtest_with_sample_data()
        
        print()
        print("💡 下一步：")
        print("  1. 使用上述方法获取真实的加密货币历史数据")
        print("  2. 修改策略参数进行优化")
        print("  3. 在不同时间段测试策略稳定性")
        print("  4. 考虑滑点和手续费的影响")
        print()
        
        print_data_acquisition_methods()
        
    except Exception as e:
        print(f"\n❌ 错误：{e}")
        import traceback
        traceback.print_exc()

