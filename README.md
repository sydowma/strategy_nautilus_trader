# Nautilus Strategy Lab

A practical NautilusTrader strategy playground for experimenting with crypto
backtests, indicator-driven entries, funding-rate ideas, and reusable report
tooling.

The repository is intentionally small: it gives you working strategy code,
sample backtests, data utilities, and enough structure to turn an idea into a
repeatable NautilusTrader experiment.

## What Is Inside

- `Strategy1`: an EMA + MACD + Camarilla pivot strategy example.
- Funding-arbitrage strategy components and simulators.
- Synthetic-data and CSV-based backtest examples.
- Binance market-data download helpers.
- HTML/report generation utilities for reviewing backtest output.

## Strategy1 At A Glance

The main example combines:

- EMA alignment for trend filtering.
- MACD crossovers for momentum confirmation.
- Camarilla pivot levels for entry/exit context.
- Configurable risk, stop-loss, and take-profit parameters.

It is meant to be a readable starting point, not a production trading system.

## Quick Start

Requirements:

- Python 3.12+
- `uv` or `pip`

Install dependencies:

```bash
uv sync
```

Or:

```bash
pip install -e .
```

Run the strategy overview:

```bash
python main.py
```

Run the synthetic-data backtest:

```bash
python examples/backtest_example.py
```

Run a crypto-oriented example:

```bash
python examples/backtest_crypto_binance.py
```

## Project Layout

```text
bot/
  bot1.py                         Strategy1 implementation
  funding_arbitrage_strategy.py   funding-rate strategy example
  ema_indicator.py                EMA helper
  macd_indicator.py               MACD helper
  pivot_point.py                  Camarilla pivot helper

examples/
  backtest_example.py             synthetic-data backtest
  backtest_crypto_binance.py      crypto backtest example
  backtest_funding_arbitrage.py   funding strategy example

tools/
  download_binance_data.py        market-data download helper
  download_funding_rate.py        funding-rate data helper
  html_report_generator.py        backtest report helper
```

## Basic Strategy Configuration

```python
from bot.bot1 import Strategy1, Strategy1Config

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

strategy = Strategy1(config=config)
```

## Customization Ideas

- Swap EMA periods to test faster or slower trend filters.
- Replace MACD confirmation with another momentum indicator.
- Add an ATR or volatility filter before allowing entries.
- Compare the same strategy across symbols and timeframes.
- Use the report utilities to inspect fills, orders, and position behavior.

## Development Checks

```bash
python -m compileall -q bot examples main.py tools
```

## Disclaimer

This repository is for research and education only. It is not financial advice
and it is not a production-ready trading system. Backtests can overfit easily,
market data can be incomplete, and live execution introduces additional risk.
Test with paper trading before risking capital.

## License

Apache License 2.0
