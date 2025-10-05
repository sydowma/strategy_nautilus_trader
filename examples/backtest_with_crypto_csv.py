"""
使用下载的加密货币 CSV 数据进行回测

此脚本展示如何使用 download_binance_data.py 下载的 CSV 数据
进行回测。
"""

import sys
import os
import pandas as pd
from decimal import Decimal

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from nautilus_trader.backtest.engine import BacktestEngine, BacktestEngineConfig
from nautilus_trader.common.enums import LogLevel
from nautilus_trader.config import LoggingConfig
from nautilus_trader.core.datetime import dt_to_unix_nanos
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

from bot.bot1 import Strategy1, Strategy1Config


def load_csv_data(csv_file: str) -> pd.DataFrame:
    """
    加载 CSV 数据文件
    
    Parameters
    ----------
    csv_file : str
        CSV文件路径
        
    Returns
    -------
    pd.DataFrame
        数据框
    """
    print(f"📂 加载数据文件：{csv_file}")
    
    df = pd.read_csv(csv_file)
    
    # 确保有 datetime 列
    if 'datetime' in df.columns:
        df['datetime'] = pd.to_datetime(df['datetime'])
    elif 'timestamp' in df.columns:
        df['datetime'] = pd.to_datetime(df['timestamp'], unit='ms')
    
    print(f"✅ 已加载 {len(df)} 条数据")
    print(f"   时间范围：{df['datetime'].min()} 至 {df['datetime'].max()}")
    print(f"   价格范围：${df['low'].min():.2f} - ${df['high'].max():.2f}")
    print()
    
    return df


def convert_to_nautilus_bars(
    df: pd.DataFrame,
    instrument_id: InstrumentId,
    bar_type: BarType
) -> list[Bar]:
    """
    将 DataFrame 转换为 NautilusTrader Bar 对象
    
    Parameters
    ----------
    df : pd.DataFrame
        包含 OHLCV 数据的 DataFrame
    instrument_id : InstrumentId
        交易对 ID
    bar_type : BarType
        Bar 类型
        
    Returns
    -------
    list[Bar]
        Bar 对象列表
    """
    print("🔄 转换数据格式...")
    
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
    
    print(f"✅ 已转换 {len(bars)} 根K线")
    print()
    
    return bars


def create_crypto_instrument(
    symbol: str = 'BTCUSDT',
    venue_name: str = 'BINANCE'
) -> CryptoPerpetual:
    """
    创建加密货币交易工具
    
    Parameters
    ----------
    symbol : str
        交易对符号（不含斜杠）
    venue_name : str
        交易所名称
        
    Returns
    -------
    CryptoPerpetual
        交易工具
    """
    venue = Venue(venue_name)
    instrument_symbol = Symbol(symbol)
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


def run_backtest_with_csv(
    csv_file: str,
    symbol: str = 'BTCUSDT',
    timeframe: str = '15m'
):
    """
    使用 CSV 数据运行回测
    
    Parameters
    ----------
    csv_file : str
        CSV 数据文件路径
    symbol : str
        交易对符号
    timeframe : str
        时间周期（用于显示）
    """
    print("=" * 80)
    print("加密货币回测 - 使用 CSV 数据")
    print("=" * 80)
    print()
    
    # 1. 加载数据
    df = load_csv_data(csv_file)
    
    # 2. 创建交易工具
    instrument = create_crypto_instrument(symbol=symbol, venue_name='BINANCE')
    venue = instrument.id.venue
    
    print(f"📊 交易配置：")
    print(f"   交易对：{instrument.id}")
    print(f"   时间周期：{timeframe}")
    print(f"   Maker 费率：{instrument.maker_fee * 100}%")
    print(f"   Taker 费率：{instrument.taker_fee * 100}%")
    print()
    
    # 3. 定义 Bar 类型
    # 解析时间周期（例如 "15m" -> 15 分钟）
    timeframe_mapping = {
        '1m': (1, BarAggregation.MINUTE),
        '5m': (5, BarAggregation.MINUTE),
        '15m': (15, BarAggregation.MINUTE),
        '30m': (30, BarAggregation.MINUTE),
        '1h': (1, BarAggregation.HOUR),
        '4h': (4, BarAggregation.HOUR),
        '1d': (1, BarAggregation.DAY),
    }
    
    step, aggregation = timeframe_mapping.get(timeframe.lower(), (15, BarAggregation.MINUTE))
    
    bar_spec = BarSpecification(
        step=step,
        aggregation=aggregation,
        price_type=PriceType.LAST,
    )
    
    bar_type = BarType(
        instrument_id=instrument.id,
        bar_spec=bar_spec,
        aggregation_source=AggregationSource.EXTERNAL,
    )
    
    # 4. 转换数据
    bars = convert_to_nautilus_bars(df, instrument.id, bar_type)
    
    # 5. 创建回测引擎
    print("⚙️ 配置回测引擎...")
    config = BacktestEngineConfig(
        logging=LoggingConfig(log_level="INFO"),
    )
    
    engine = BacktestEngine(config=config)
    
    # 6. 添加交易所
    engine.add_venue(
        venue=venue,
        oms_type=OmsType.NETTING,
        account_type=AccountType.MARGIN,
        base_currency=USDT,
        starting_balances=[Money(10000, USDT)],  # 初始 10,000 USDT
    )
    
    # 7. 添加交易工具和数据
    engine.add_instrument(instrument)
    engine.add_data(bars)
    
    print(f"   初始资金：10,000 USDT")
    print()
    
    # 8. 配置策略
    print("🎯 配置交易策略...")
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
    
    print(f"   EMA 周期：{strategy_config.ema_periods}")
    print(f"   MACD：{strategy_config.macd_fast_period}/{strategy_config.macd_slow_period}/{strategy_config.macd_signal_period}")
    print(f"   每笔风险：{strategy_config.risk_percent * 100}%")
    print(f"   止损：-2% | 止盈：+4%")
    print()
    
    # 9. 添加策略
    strategy = Strategy1(config=strategy_config)
    engine.add_strategy(strategy)
    
    # 10. 运行回测
    print("=" * 80)
    print("🚀 开始回测...")
    print("=" * 80)
    print()
    
    engine.run()
    
    print()
    print("=" * 80)
    print("✅ 回测完成！")
    print("=" * 80)
    print()
    
    # 11. 显示结果
    print("📊 回测结果：")
    print("=" * 80)
    
    account_report = engine.trader.generate_account_report(venue)
    print("\n💰 账户报告：")
    print("-" * 80)
    print(account_report)
    
    orders_report = engine.trader.generate_orders_report()
    if orders_report is not None and not orders_report.empty:
        print("\n📝 订单报告：")
        print("-" * 80)
        print(orders_report)
    else:
        print("\n📝 未产生任何交易订单")
    
    positions_report = engine.trader.generate_positions_report()
    if positions_report is not None and not positions_report.empty:
        print("\n📈 持仓报告：")
        print("-" * 80)
        print(positions_report)
    else:
        print("\n📈 未开仓任何头寸")
    
    fills_report = engine.trader.generate_order_fills_report()
    if fills_report is not None and not fills_report.empty:
        print("\n✅ 成交报告：")
        print("-" * 80)
        print(fills_report)
    
    print()
    print("=" * 80)


def main():
    """主函数"""
    
    # 查找数据文件
    data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'binance')
    
    if os.path.exists(data_dir):
        csv_files = [f for f in os.listdir(data_dir) if f.endswith('.csv')]
        
        if csv_files:
            print("\n可用的数据文件：")
            for i, f in enumerate(csv_files, 1):
                print(f"  {i}. {f}")
            
            print()
            choice = input(f"选择文件 (1-{len(csv_files)}) [默认=1]: ").strip() or "1"
            
            try:
                idx = int(choice) - 1
                if 0 <= idx < len(csv_files):
                    csv_file = os.path.join(data_dir, csv_files[idx])
                    
                    # 从文件名解析参数
                    filename = csv_files[idx]
                    parts = filename.replace('.csv', '').split('_')
                    symbol = parts[0].upper() if parts else 'BTCUSDT'
                    timeframe = parts[1] if len(parts) > 1 else '15m'
                    
                    run_backtest_with_csv(csv_file, symbol=symbol, timeframe=timeframe)
                else:
                    print("❌ 无效的选择")
            except (ValueError, IndexError) as e:
                print(f"❌ 无效的输入: {e}")
        else:
            print("\n❌ 未找到数据文件")
            print("\n💡 请先运行以下命令下载数据：")
            print("   python tools/download_binance_data.py")
    else:
        print("\n❌ 数据目录不存在")
        print("\n💡 请先运行以下命令下载数据：")
        print("   python tools/download_binance_data.py")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n❌ 错误：{e}")
        import traceback
        traceback.print_exc()

