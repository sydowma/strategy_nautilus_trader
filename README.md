# Strategy Nautilus Trader

A comprehensive trading strategy implementation using the NautilusTrader framework, featuring multiple technical indicators and backtesting capabilities.

## 📋 Overview

This project implements **Strategy1**, a multi-indicator trading strategy that combines:

- **EMA (Exponential Moving Average)** - Trend identification with multiple periods (20, 50, 100, 200)
- **MACD (Moving Average Convergence Divergence)** - Momentum signals and trend reversals
- **Camarilla Pivot Points** - Support and resistance levels for entry/exit optimization

## 🎯 Trading Strategy

### Entry Signals

**Long Entry:**
- EMA indicators show uptrend (faster EMAs above slower EMAs)
- MACD bullish crossover (MACD line crosses above signal line)
- Price near support level (within 0.5% of S1 or S2 pivot points)

**Short Entry:**
- EMA indicators show downtrend
- MACD bearish crossover (MACD line crosses below signal line)
- Price near resistance level (within 0.5% of R1 or R2 pivot points)

### Exit Signals

- **Stop Loss**: -2% from entry price
- **Take Profit**: +4% from entry price (2:1 risk/reward ratio)
- **MACD Reversal**: Opposite MACD crossover

## 📁 Project Structure

```
strategy_nautilus_trader/
├── bot/
│   ├── __init__.py
│   ├── bot1.py              # Main strategy implementation
│   ├── ema_indicator.py     # EMA indicator calculations
│   ├── macd_indicator.py    # MACD indicator calculations
│   └── pivot_point.py       # Camarilla pivot points
├── examples/
│   └── backtest_example.py  # Complete backtest example
├── main.py                  # Entry point and usage guide
├── pyproject.toml           # Project dependencies
└── README.md                # This file
```

## 🚀 Getting Started

### Prerequisites

- Python 3.12 or higher
- NautilusTrader 1.220.0 or higher

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd strategy_nautilus_trader
```

2. Install dependencies using `uv` (recommended):
```bash
uv sync
```

Or using pip:
```bash
pip install -e .
```

### Quick Start

1. Run the demo to see strategy configuration:
```bash
python main.py
```

2. Run a complete backtest with synthetic data:
```bash
python examples/backtest_example.py
```

3. Run backtest with real historical data (if you have CSV data):
```bash
python examples/backtest_with_real_data.py
```

## 💻 Usage

### Basic Strategy Configuration

```python
from bot.bot1 import Strategy1, Strategy1Config

# Configure the strategy
config = Strategy1Config(
    instrument_id="BTCUSDT-PERP.BINANCE",
    bar_type="BTCUSDT-PERP.BINANCE-15-MINUTE-LAST-EXTERNAL",
    ema_periods=[20, 50, 100, 200],
    macd_fast_period=12,
    macd_slow_period=26,
    macd_signal_period=9,
    risk_percent=0.01,
    stop_loss_atr_multiplier=2.0,
    take_profit_risk_reward=2.0,
)

# Create strategy instance
strategy = Strategy1(config=config)
```

### Running a Backtest

```python
from nautilus_trader.backtest.engine import BacktestEngine, BacktestEngineConfig
from nautilus_trader.model.enums import AccountType, OmsType
from nautilus_trader.model.objects import Money
from nautilus_trader.model.currencies import USD

# Create backtest engine
engine = BacktestEngine(
    config=BacktestEngineConfig(logging=LogLevel.INFO)
)

# Add venue configuration
engine.add_venue(
    venue=Venue("BINANCE"),
    oms_type=OmsType.NETTING,
    account_type=AccountType.MARGIN,
    base_currency=USD,
    starting_balances=[Money(100000, USD)],
)

# Add instruments and data
engine.add_instrument(instrument)
engine.add_bars(bars)  # Your historical bar data

# Add strategy
engine.add_strategy(strategy)

# Run backtest
engine.run()

# Generate reports
print(engine.trader.generate_account_report(venue))
print(engine.trader.generate_orders_report())
```

## 📊 Indicators

### EMA (Exponential Moving Average)

The strategy uses multiple EMA periods to identify trends:
- **20-period EMA**: Fast-moving average for short-term trend
- **50-period EMA**: Medium-term trend
- **100-period EMA**: Long-term trend
- **200-period EMA**: Major trend identifier

**Trend Confirmation**: Price and all EMAs must be aligned (uptrend: EMA20 > EMA50 > EMA100 > EMA200)

### MACD (Moving Average Convergence Divergence)

Standard MACD configuration:
- **Fast EMA**: 12 periods
- **Slow EMA**: 26 periods
- **Signal Line**: 9-period EMA of MACD line
- **Histogram**: MACD line - Signal line

**Signals**:
- Bullish crossover: MACD crosses above signal line
- Bearish crossover: MACD crosses below signal line

### Camarilla Pivot Points

Calculates support (S1-S5) and resistance (R1-R5) levels based on previous period's high, low, and close prices.

**Formula**:
- PP = (High + Low + Close) / 3
- R1 = Close + Range × 1.1/12
- S1 = Close - Range × 1.1/12
- (Additional levels calculated similarly)

## ⚙️ Configuration Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `instrument_id` | str | Required | Trading instrument identifier |
| `bar_type` | str | Required | Bar type specification |
| `ema_periods` | list[int] | [20, 50, 100, 200] | EMA periods for trend analysis |
| `macd_fast_period` | int | 12 | MACD fast EMA period |
| `macd_slow_period` | int | 26 | MACD slow EMA period |
| `macd_signal_period` | int | 9 | MACD signal line period |
| `risk_percent` | float | 0.01 | Risk per trade (1%) |
| `stop_loss_atr_multiplier` | float | 2.0 | Stop loss distance |
| `take_profit_risk_reward` | float | 2.0 | Risk/reward ratio |

## 🧪 Testing

### Synthetic Data Backtest

The project includes a complete backtest example with synthetic data generation. Run it to test the strategy:

```bash
python examples/backtest_example.py
```

This will:
1. Generate 1000 bars of synthetic OHLCV data
2. Run Strategy1 with default parameters
3. Display backtest results and performance metrics

### Real Historical Data Backtest

You can use real market data for more accurate backtesting:

1. **Place your CSV data file** in the project root:
   - Supported format: `DAT_ASCII_EURUSD_T_202001.csv.gz`
   - Format: `timestamp,bid,ask,volume`
   - Timestamp format: `YYYYMMDD HHMMSSMMM`

2. **Run the real data backtest**:
   ```bash
   python examples/backtest_with_real_data.py
   ```

3. **The script will**:
   - Load and parse the compressed CSV file
   - Convert tick data to 15-minute bars
   - Run Strategy1 with the historical data
   - Generate comprehensive performance reports

**Example data sources:**
- [Dukascopy Historical Data](https://www.dukascopy.com/swiss/english/marketwatch/historical/)
- [HistData.com](http://www.histdata.com/)
- [TrueFX Historical Data](https://www.truefx.com/)

## 📈 Performance Metrics

After running a backtest, you'll receive:

- **Account Report**: Final balance, PnL, returns
- **Positions Report**: All opened positions with entry/exit details
- **Orders Report**: All orders executed during the backtest
- **Fills Report**: Order fill details and execution prices

## 🔧 Customization

### Adjusting Indicator Parameters

Modify the strategy configuration to test different parameters:

```python
config = Strategy1Config(
    instrument_id="BTCUSDT-PERP.BINANCE",
    bar_type="BTCUSDT-PERP.BINANCE-5-MINUTE-LAST-EXTERNAL",  # Change timeframe
    ema_periods=[10, 20, 50],  # Use fewer/different EMAs
    macd_fast_period=8,        # Faster MACD
    risk_percent=0.02,         # Increase risk to 2%
)
```

### Adding New Indicators

1. Create a new indicator file in `bot/`:
```python
# bot/my_indicator.py
class MyIndicator:
    def __init__(self, period: int):
        self.period = period
    
    def calculate(self, data: list[float]) -> list[float]:
        # Your indicator logic
        pass
```

2. Import and use in `bot1.py`:
```python
from bot.my_indicator import MyIndicator

class Strategy1(Strategy):
    def __init__(self, config: Strategy1Config):
        super().__init__(config)
        self.my_indicator = MyIndicator(period=14)
```

## 📚 Resources

- [NautilusTrader Documentation](https://nautilustrader.io/docs/)
- [NautilusTrader Backtesting Guide](https://nautilustrader.io/docs/latest/concepts/backtesting)
- [NautilusTrader GitHub](https://github.com/nautechsystems/nautilus_trader)

## ⚠️ Disclaimer

This software is for educational purposes only. **Do not risk money which you are afraid to lose.** USE THE SOFTWARE AT YOUR OWN RISK. THE AUTHORS AND ALL AFFILIATES ASSUME NO RESPONSIBILITY FOR YOUR TRADING RESULTS.

Always test strategies thoroughly with paper trading before deploying with real capital.

## 📝 License

This project is provided as-is for educational purposes.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📧 Support

For questions or issues, please open an issue on the GitHub repository.
