# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

Two standalone, long-running Python scripts that scan stock indices for SMA5/SMA20 golden/dead crosses and push alerts to Telegram:

- `kospi.py` — KOSPI 200, data from `pykrx` (`stock.get_market_ohlcv_by_date`, column `종가`)
- `snp500.py` — S&P 500, data from `yfinance` (`yf.download`, column `Close`)

There is no shared module, no package structure, no tests, and no linter config. Each script is self-contained.

## Commands

```bash
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt

# Run in foreground
python3 snp500.py
python3 kospi.py

# Run as background daemon (as in README; output_files/logs/ must exist first)
nohup python3 snp500.py > output_files/logs/nohup.out 2>&1 &
nohup python3 kospi.py  > output_files/logs/nohup.out 2>&1 &
```

To exercise a single ticker without the infinite loop, import the module and call `check_cross` directly (the main loop is behind `if __name__ == "__main__"`), e.g. `python3 -c "import snp500; print(snp500.check_cross('AAPL'))"`. Note `snp500.py` configures file logging at import time.

## Required environment variables

- `SNP500_GOLDEN_DEAD_CROSS_TELEGRAM_BOT_TOKEN`, `SNP500_GOLDEN_DEAD_CROSS_TELEGRAM_CHAT_ID`
- `KOSPI_GOLDEN_DEAD_CROSS_TELEGRAM_BOT_TOKEN`, `KOSPI_GOLDEN_DEAD_CROSS_TELEGRAM_CHAT_ID`

`snp500.py` skips sending if unset; `kospi.py` does not check and will just get a Telegram error.

## Architecture (both scripts follow the same shape)

1. **Ticker source** — `get_kospi200_tickers()` parses a hardcoded `name , code` block (edit it to change the universe); `get_sp500_tickers()` scrapes the Wikipedia S&P 500 table via `pd.read_html` on every call. `fix_ticker` converts `.` → `-` for yfinance (e.g. `BRK.B` → `BRK-B`).
2. **`check_cross(ticker)`** — returns `('golden'|'dead'|None, price)`; `(None, None)` signals failure. A cross means yesterday's SMA5 vs SMA20 ordering flipped today. Failures are appended to `failed_tickers.log` / `failed_kospi_tickers.log`.
3. **`run_cross_check()`** — iterates all tickers sequentially and sends one Telegram message per cross via `send_alert_once`, which skips `"{ticker}:{golden|dead}"` keys already sent for the session date. Sent keys persist in `snp500_sent_alerts.json` / `kospi_sent_alerts.json` (`{"date", "sent"}`; reset when the date changes) so restarts don't resend. The session date is the New York date for snp500 and local date for kospi. A key is recorded only if `send_telegram_message` returns `True`. snp500 sends a summary only when the scan newly alerted at least one signal (`send_alert_once` returns `True` for new sends).
4. **`should_run_now()`** — trading-hours gate:
   - KOSPI: weekdays 09:00–15:59 in local machine time (assumes the server runs in KST)
   - S&P 500: converts to `America/New_York` via `zoneinfo` and checks weekdays 09:30–16:00 (`NY_TZ`, `MARKET_OPEN`, `MARKET_CLOSE`), so DST and the KST/US date offset are handled regardless of server timezone. US holidays are not excluded. Accepts an optional `now` argument (aware datetime) for testing. `datetime.time` is imported as `dtime` because the `time` module is also used.
5. **Main loop** — starts a daemon heartbeat thread (Telegram message every 3600s), then checks `should_run_now()` every 600s forever.

## Differences between the scripts worth knowing

- `snp500.py` uses the `logging` module (→ `snp500_monitor.log` + stdout) and sends start/stop/error Telegram messages; `kospi.py` uses `print` and has none of that.
- yfinance returns MultiIndex columns even for a single ticker, so `snp500.py` extracts scalars with `.iloc[0]` (e.g. `today['Close'].iloc[0]`). `pykrx` rows are plain, so `kospi.py` indexes directly.
- `kospi.py` fetches 365 days and requires ≥200 rows; `snp500.py` fetches `3mo` and requires ≥25.

## Conventions

- 2-space indentation; Korean comments and Korean/emoji Telegram messages (HTML `parse_mode`).
- `*.log` files are gitignored.
