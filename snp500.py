import json
import logging
import os
import threading
import time
from datetime import datetime, time as dtime
from zoneinfo import ZoneInfo

import pandas as pd
import requests
import yfinance as yf

# Logging 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
      logging.FileHandler('snp500_monitor.log', encoding='utf-8'),
      logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Telegram 설정
TELEGRAM_TOKEN = os.getenv('SNP500_GOLDEN_DEAD_CROSS_TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('SNP500_GOLDEN_DEAD_CROSS_TELEGRAM_CHAT_ID')

# 미국 정규장 (뉴욕 시간)
NY_TZ = ZoneInfo('America/New_York')
MARKET_OPEN = dtime(9, 30)
MARKET_CLOSE = dtime(16, 0)

# 당일 이미 보낸 알림 기록 (같은 신호 중복 전송 방지)
SENT_ALERTS_FILE = 'snp500_sent_alerts.json'


def fix_ticker(ticker):
  return ticker.replace('.', '-')


# S&P500 종목과 영문 회사명 가져오기
def get_sp500_tickers():
  try:
    url = 'https://en.wikipedia.org/wiki/List_of_S%26P_500_companies'
    tables = pd.read_html(url)
    df = tables[0]
    logger.info(f"Retrieved {len(df['Symbol'])} S&P 500 tickers")
    return list(zip(df['Symbol'], df['Security']))
  except Exception as e:
    logger.error(f"Failed to fetch S&P 500 tickers: {e}")
    return []


# 골든크로스/데드크로스 확인
def check_cross(ticker):
  try:
    df = yf.download(ticker, period="3mo", interval="1d", progress=False,
                     auto_adjust=False)

    if df is None or len(df) == 0:
      logger.warning(f"{ticker}: No data received")
      return None, None

    if len(df) < 25:
      logger.warning(
          f"{ticker}: Insufficient data (length={len(df)}, need at least 25)")
      return None, None

    if 'Close' not in df.columns:
      logger.warning(f"{ticker}: Close column not found in data")
      return None, None

    df['SMA5'] = df['Close'].rolling(window=5).mean()
    df['SMA20'] = df['Close'].rolling(window=20).mean()
    df.dropna(inplace=True)

    if len(df) < 2:
      logger.warning(
          f"{ticker}: Not enough data after calculating moving averages (length={len(df)})")
      return None, None

    yesterday = df.iloc[-2]
    today = df.iloc[-1]

    price = float(today['Close'].iloc[0])
    today_sma5 = float(today['SMA5'].iloc[0])
    today_sma20 = float(today['SMA20'].iloc[0])
    yesterday_sma5 = float(yesterday['SMA5'].iloc[0])
    yesterday_sma20 = float(yesterday['SMA20'].iloc[0])

    if yesterday_sma5 < yesterday_sma20 and today_sma5 > today_sma20:
      logger.info(
          f"{ticker}: Golden Cross detected (SMA5: {today_sma5:.2f}, SMA20: {today_sma20:.2f})")
      return 'golden', price
    elif yesterday_sma5 > yesterday_sma20 and today_sma5 < today_sma20:
      logger.info(
          f"{ticker}: Dead Cross detected (SMA5: {today_sma5:.2f}, SMA20: {today_sma20:.2f})")
      return 'dead', price
    else:
      logger.debug(
          f"{ticker}: No cross detected (SMA5={today_sma5:.2f}, SMA20={today_sma20:.2f})")
      return None, price

  except Exception as e:
    logger.error(f"{ticker}: Error in check_cross: {e}")
    with open("failed_tickers.log", "a") as f:
      f.write(f"{datetime.now()} - {ticker}: {e}\n")
    return None, None


# 텔레그램 메시지 전송
def send_telegram_message(message):
  if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
    logger.warning("Telegram credentials not set - message not sent")
    return False

  url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
  payload = {
    'chat_id': TELEGRAM_CHAT_ID,
    'text': message,
    'parse_mode': 'HTML'
  }
  try:
    response = requests.post(url, data=payload, timeout=10)
    if response.status_code != 200:
      logger.error(f"Telegram error: {response.text}")
      return False
    logger.debug("Telegram message sent successfully")
    return True
  except Exception as e:
    logger.error(f"Telegram exception: {e}")
    return False


# 당일 보낸 알림 불러오기 (날짜가 바뀌면 빈 기록으로 시작)
def load_sent_alerts(session_date):
  try:
    with open(SENT_ALERTS_FILE, encoding='utf-8') as f:
      data = json.load(f)
    if data.get('date') == session_date:
      return set(data.get('sent', []))
  except FileNotFoundError:
    pass
  except Exception as e:
    logger.warning(f"Failed to load {SENT_ALERTS_FILE}: {e}")
  return set()


def save_sent_alerts(session_date, sent_alerts):
  try:
    with open(SENT_ALERTS_FILE, 'w', encoding='utf-8') as f:
      json.dump({'date': session_date, 'sent': sorted(sent_alerts)}, f)
  except Exception as e:
    logger.warning(f"Failed to save {SENT_ALERTS_FILE}: {e}")


# 같은 날 같은 종목·신호는 한 번만 전송 (새로 보냈으면 True)
def send_alert_once(sent_alerts, session_date, key, message):
  if key in sent_alerts:
    logger.info(f"{key}: already alerted on {session_date} - skipped")
    return False
  if send_telegram_message(message):
    sent_alerts.add(key)
    save_sent_alerts(session_date, sent_alerts)
    return True
  return False


# Heartbeat 기능
def start_heartbeat(heartbeat_interval=3600):
  def _send_heartbeat():
    while True:
      message = (
        f"💓 <b>S&P 500 모니터링 Heartbeat</b>\n\n"
        f"🕒 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        f"📊 상태: 정상 작동 중\n"
        f"🎯 모니터링 종목: {len(get_sp500_tickers())}개 (S&P 500)\n"
        f"⏰ 다음 점검: 10분 후"
      )
      send_telegram_message(message)
      logger.info(f"💓 Heartbeat sent")
      time.sleep(heartbeat_interval)

  heartbeat_thread = threading.Thread(target=_send_heartbeat, daemon=True)
  heartbeat_thread.start()
  logger.info("✅ Heartbeat thread started")


# 전체 점검 루틴
def run_cross_check():
  logger.info(
      f"Running check at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
  ticker_pairs = get_sp500_tickers()
  total = len(ticker_pairs)
  start_time = time.time()

  golden_crosses = []
  dead_crosses = []
  new_golden_count = 0
  new_dead_count = 0
  failed_count = 0

  # 미국장 기준 날짜 (뉴욕 시간)
  session_date = datetime.now(NY_TZ).strftime('%Y-%m-%d')
  sent_alerts = load_sent_alerts(session_date)

  for i, (ticker, company_name) in enumerate(ticker_pairs):
    ticker_start = time.time()
    fixed_ticker = fix_ticker(ticker)
    result, price = check_cross(fixed_ticker)

    if result == 'golden':
      golden_crosses.append((ticker, price))
      msg = (
        f"📈 <b>{ticker}</b> ({company_name})\n"
        f"➡️ <b>Golden Cross</b> 발생\n"
        f"💰 현재가: ${price:.2f}\n"
        f"🕒 {datetime.now().strftime('%Y-%m-%d %H:%M')}"
      )
      logger.info(f"Golden Cross: {ticker} ({company_name})")
      if send_alert_once(sent_alerts, session_date, f"{ticker}:golden", msg):
        new_golden_count += 1
    elif result == 'dead':
      dead_crosses.append((ticker, price))
      msg = (
        f"📉 <b>{ticker}</b> ({company_name})\n"
        f"➡️ <b>Dead Cross</b> 발생\n"
        f"💰 현재가: ${price:.2f}\n"
        f"🕒 {datetime.now().strftime('%Y-%m-%d %H:%M')}"
      )
      logger.info(f"Dead Cross: {ticker} ({company_name})")
      if send_alert_once(sent_alerts, session_date, f"{ticker}:dead", msg):
        new_dead_count += 1
    elif price is None:
      failed_count += 1

    ticker_elapsed = time.time() - ticker_start
    total_elapsed = time.time() - start_time
    price_str = f"${price:.2f}" if price is not None else "가격 정보 없음"

    logger.info(
        f"[{i + 1}/{total}] {ticker} - {result or 'None'}. Price: {price_str}. "
        f"⏱ Ticker: {ticker_elapsed:.2f}s | Total: {total_elapsed:.2f}s")

  logger.info(
      f"Scan completed. Golden: {len(golden_crosses)} (new {new_golden_count}), "
      f"Dead: {len(dead_crosses)} (new {new_dead_count}), Failed: {failed_count}")

  # 새로 알린 신호가 있을 때만 요약 전송
  if new_golden_count == 0 and new_dead_count == 0:
    logger.info("No new signals - summary not sent")
    return

  summary_msg = (
    f"📊 <b>S&P 500 스캔 완료</b>\n\n"
    f"🕒 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
    f"📈 Golden Cross: {len(golden_crosses)}개 (신규 {new_golden_count})\n"
    f"📉 Dead Cross: {len(dead_crosses)}개 (신규 {new_dead_count})\n"
    f"❌ 실패: {failed_count}개\n"
    f"⏱ 총 소요시간: {time.time() - start_time:.1f}초"
  )
  send_telegram_message(summary_msg)


def should_run_now(now=None):
  # 미국 동부 시간 기준으로 판단하므로 서머타임과 요일이 자동으로 반영됨
  now = (now or datetime.now(NY_TZ)).astimezone(NY_TZ)
  is_weekday = now.weekday() < 5  # Monday to Friday
  is_trading_hours = MARKET_OPEN <= now.time() < MARKET_CLOSE
  return is_weekday and is_trading_hours


if __name__ == "__main__":
  try:
    start_msg = (
      f"🚀 <b>S&P 500 모니터링 시작</b>\n\n"
      f"🕒 시작 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
      f"📊 모니터링 주기: 10분\n"
      f"💓 Heartbeat: 1시간마다"
    )
    send_telegram_message(start_msg)

    start_heartbeat(heartbeat_interval=3600)

    while True:
      if should_run_now():
        run_cross_check()
      else:
        logger.info(
            f"Skip: Not in target time ({datetime.now().strftime('%Y-%m-%d %H:%M:%S')})")
      time.sleep(600)

  except KeyboardInterrupt:
    logger.info("프로그램이 사용자에 의해 중단되었습니다.")
    stop_msg = f"⏹ <b>S&P 500 모니터링 중단</b>\n🕒 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    send_telegram_message(stop_msg)
  except Exception as e:
    logger.error(f"Main loop error: {e}")
    error_msg = f"❌ <b>시스템 오류 발생</b>\n🕒 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n📝 {str(e)}"
    send_telegram_message(error_msg)
    with open("snp500_error.log", "a") as f:
      f.write(f"{datetime.now()} - Main loop error: {e}\n")
