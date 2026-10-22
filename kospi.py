import holidays
import json
import os
import requests
import threading
import time
from datetime import datetime, timedelta
from pykrx import stock

# ===== 텔레그램 설정 =====
TELEGRAM_TOKEN = os.getenv('KOSPI_GOLDEN_DEAD_CROSS_TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('KOSPI_GOLDEN_DEAD_CROSS_TELEGRAM_CHAT_ID')

# 당일 이미 보낸 알림 기록 (같은 신호 중복 전송 방지)
SENT_ALERTS_FILE = 'kospi_sent_alerts.json'

# 한국거래소 휴장일 (연도는 조회할 때 자동으로 확장됨)
KRX_HOLIDAYS = holidays.XKRX()


# ===== 하드코딩된 KOSPI200 일부 (전체 확장 가능) =====
def get_kospi200_tickers():
  raw = """
    삼성전자	,	005930
    SK하이닉스	,	000660
    LG에너지솔루션	,	373220
    삼성바이오로직스	,	207940
    한화에어로스페이스	,	012450
    현대차	,	005380
    삼성전자우	,	005935
    KB금융	,	105560
    기아	,	000270
    두산에너빌리티	,	034020
    셀트리온	,	068270
    NAVER	,	035420
    HD현대중공업	,	329180
    신한지주	,	055550
    삼성물산	,	028260
    현대모비스	,	012330
    POSCO홀딩스	,	005490
    삼성생명	,	032830
    하나금융지주	,	086790
    한화오션	,	042660
    HMM	,	011200
    카카오	,	035720
    한국전력	,	015760
    HD한국조선해양	,	009540
    삼성화재	,	000810
    메리츠금융지주	,	138040
    현대로템	,	064350
    LG화학	,	051910
    SK스퀘어	,	402340
    우리금융지주	,	316140
    SK이노베이션	,	096770
    HD현대일렉트릭	,	267260
    삼성중공업	,	010140
    고려아연	,	010130
    크래프톤	,	259960
    KT&G	,	033780
    기업은행	,	024110
    SK	,	034730
    삼성SDI	,	006400
    KT	,	030200
    카카오뱅크	,	323410
    삼성에스디에스	,	018260
    LIG넥스원	,	079550
    LG전자	,	066570
    LG	,	003550
    SK텔레콤	,	017670
    포스코퓨처엠	,	003670
    미래에셋증권	,	006800
    하이브	,	352820
    HD현대	,	267250
    현대글로비스	,	086280
    한화시스템	,	272210
    삼양식품	,	003230
    삼성전기	,	009150
    유한양행	,	000100
    포스코인터내셔널	,	047050
    효성중공업	,	298040
    DB손해보험	,	005830
    대한항공	,	003490
    두산	,	000150
    한국항공우주	,	047810
    LS ELECTRIC	,	010120
    한국금융지주	,	071050
    한미반도체	,	042700
    HD현대마린솔루션	,	443060
    SK바이오팜	,	326030
    코웨이	,	021240
    아모레퍼시픽	,	090430
    카카오페이	,	377300
    한진칼	,	180640
    HD현대미포	,	010620
    현대건설	,	000720
    S-Oil	,	010950
    한화	,	000880
    LG씨엔에스	,	064400
    에이피알	,	278470
    NH투자증권	,	005940
    한화솔루션	,	009830
    LG유플러스	,	032640
    삼성증권	,	016360
    삼성카드	,	029780
    현대차2우B	,	005387
    한국타이어앤테크놀로지	,	161390
    키움증권	,	039490
    LS	,	006260
    맥쿼리인프라	,	088980
    두산밥캣	,	241560
    넷마블	,	251270
    LG생활건강	,	051900
    현대제철	,	004020
    삼성E&A	,	028050
    BNK금융지주	,	138930
    GS	,	078930
    JB금융지주	,	175330
    LG디스플레이	,	034220
    CJ	,	001040
    풍산	,	103140
    오리온	,	271560
    현대오토에버	,	307950
    이수페타시스	,	007660
    엔씨소프트	,	036570
    강원랜드	,	035250
    한국가스공사	,	036460
    포스코DX	,	022100
    두산로보틱스	,	454910
    SKC	,	011790
    현대차우	,	005385
    CJ제일제당	,	097950
    SK바이오사이언스	,	302440
    한미약품	,	128940
    에코프로머티	,	450080
    LG이노텍	,	011070
    금호석유화학	,	011780
    한미사이언스	,	008930
    한전기술	,	052690
    KCC	,	002380
    현대엘리베이터	,	017800
    한화생명	,	088350
    롯데지주	,	004990
    동서	,	026960
    대한전선	,	001440
    산일전기	,	062040
    F&F	,	383220
    서울보증보험	,	031210
    롯데케미칼	,	011170
    한화비전	,	489790
    코스맥스	,	192820
    에스원	,	012750
    영원무역	,	111770
    SK가스	,	018670
    달바글로벌	,	483650
    시프트업	,	462870
    아모레퍼시픽홀딩스	,	002790
    이마트	,	139480
    한화엔진	,	082740
    제일기획	,	030000
    더존비즈온	,	012510
    iM금융지주	,	139130
    농심	,	004370
    한국앤컴퍼니	,	000240
    현대해상	,	001450
    한전KPS	,	051600
    신영증권	,	001720
    팬오션	,	028670
    HD현대인프라코어	,	042670
    한온시스템	,	018880
    한국콜마	,	161890
    미스토홀딩스	,	081660
    엘앤에프	,	066970
    코리안리	,	003690
    씨에스윈드	,	112610
    롯데쇼핑	,	023530
    CJ대한통운	,	000120
    SK아이이테크놀로지	,	361610
    BGF리테일	,	282332
    호텔신라	,	008770
    DB하이텍	,	000990
    아시아나항공	,	020560
    한솔케미칼	,	014680
    대웅제약	,	069620
    HD현대마린엔진	,	071970
    동원산업	,	006040
    DL이앤씨	,	375500
    일진전기	,	103590
    OCI홀딩스	,	010060
    영원무역홀딩스	,	009970
    녹십자	,	006280
    신세계	,	004170
    파라다이스	,	034230
    HL만도	,	204320
    GS건설	,	006360
    현대백화점	,	069960
    DN오토모티브	,	007340
    SNT다이내믹스	,	003570
    에스엘	,	005850
    엠앤씨솔루션	,	484870
    대우건설	,	047040
    다우기술	,	023590
    오뚜기	,	007310
    HDC현대산업개발	,	294870
    한올바이오파마	,	009420
    두산우	,	000155
    대웅	,	003090
    오리온홀딩스	,	001800
    하이트진로	,	000080
    두산퓨얼셀	,	336260
    현대위아	,	011210
    GS리테일	,	007070
    동양생명	,	082640
    현대지에프홀딩스	,	005440
    대신증권	,	003540
    SK리츠	,	395400
    한국카본	,	017960
    이수스페셜티케미컬	,	457190
    금호타이어	,	073240
    HD현대건설기계	,	267270
    롯데관광개발	,	032350
    한화투자증권	,	003530
    HDC	,	012630
    롯데에너지머티리얼즈	,	020150
    """

  lst = []
  for line in raw.strip().splitlines():
    name, code = map(str.strip, line.split(','))
    lst.append((name, code))
  return lst


# ===== 골든/데드크로스 판단 =====
def check_cross(ticker):
  try:
    end = datetime.today()
    start = end - timedelta(days=365)
    df = stock.get_market_ohlcv_by_date(start.strftime("%Y%m%d"),
                                        end.strftime("%Y%m%d"), ticker)

    if df.empty or len(df) < 200:
      raise ValueError("Not enough data")

    df['SMA5'] = df['종가'].rolling(window=5).mean()
    df['SMA20'] = df['종가'].rolling(window=20).mean()
    df.dropna(inplace=True)

    if len(df) < 2:
      return None, None

    yesterday = df.iloc[-2]
    today = df.iloc[-1]

    price = today['종가']

    if yesterday['SMA5'] < yesterday['SMA20'] and today['SMA5'] > today[
      'SMA20']:
      return 'golden', price
    elif yesterday['SMA5'] > yesterday['SMA20'] and today['SMA5'] < today[
      'SMA20']:
      return 'dead', price
    else:
      return None, price
  except Exception as e:
    print(f"[!] Error with {ticker}: {e}")
    with open("failed_kospi_tickers.log", "a") as f:
      f.write(f"{datetime.now()} - {ticker} - {e}\n")
    return None, None


# ===== 텔레그램 전송 =====
def send_telegram_message(message):
  url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
  payload = {
    'chat_id': TELEGRAM_CHAT_ID,
    'text': message,
    'parse_mode': 'HTML'
  }
  try:
    response = requests.post(url, data=payload)
    if response.status_code != 200:
      print("Telegram error:", response.text)
      return False
    return True
  except Exception as e:
    print(f"Telegram exception: {e}")
    return False


# ===== 중복 알림 방지 =====
def load_sent_alerts(session_date):
  """당일 보낸 알림 불러오기 (날짜가 바뀌면 빈 기록으로 시작)"""
  try:
    with open(SENT_ALERTS_FILE, encoding='utf-8') as f:
      data = json.load(f)
    if data.get('date') == session_date:
      return set(data.get('sent', []))
  except FileNotFoundError:
    pass
  except Exception as e:
    print(f"[!] Failed to load {SENT_ALERTS_FILE}: {e}")
  return set()


def save_sent_alerts(session_date, sent_alerts):
  try:
    with open(SENT_ALERTS_FILE, 'w', encoding='utf-8') as f:
      json.dump({'date': session_date, 'sent': sorted(sent_alerts)}, f)
  except Exception as e:
    print(f"[!] Failed to save {SENT_ALERTS_FILE}: {e}")


def send_alert_once(sent_alerts, session_date, key, message):
  """같은 날 같은 종목·신호는 한 번만 전송"""
  if key in sent_alerts:
    print(f"{key}: already alerted on {session_date} - skipped")
    return
  if send_telegram_message(message):
    sent_alerts.add(key)
    save_sent_alerts(session_date, sent_alerts)


# ===== Heartbeat 기능 =====
def start_heartbeat(heartbeat_interval=3600):
  """1시간마다 Heartbeat 메시지를 전송하는 스레드 시작"""

  def _send_heartbeat():
    while True:
      message = (
        f"💓 <b>KOSPI 200 모니터링 Heartbeat</b>\n\n"
        f"🕒 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        f"📊 상태: 정상 작동 중\n"
        f"🎯 모니터링 종목: {len(get_kospi200_tickers())}개 (KOSPI 200)\n"
        f"⏰ 다음 점검: 10분 후"
      )
      send_telegram_message(message)
      print(
          f"💓 Heartbeat sent at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
      time.sleep(heartbeat_interval)

  heartbeat_thread = threading.Thread(target=_send_heartbeat, daemon=True)
  heartbeat_thread.start()
  print("✅ Heartbeat thread started")


# ===== 점검 루틴 =====
def run_cross_check():
  print(f"\n📅 Running check at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
  tickers = get_kospi200_tickers()
  total = len(tickers)
  start_time = time.time()
  fail_count = 0
  session_date = datetime.now().strftime('%Y-%m-%d')
  sent_alerts = load_sent_alerts(session_date)

  for i, (name, ticker) in enumerate(tickers):
    ticker_start = time.time()
    result, price = check_cross(ticker)
    if result:
      msg = (
        f"📈 <b>{name} ({ticker})</b> has a <b>{'Golden' if result == 'golden' else 'Dead'} Cross</b> signal.\n"
        f"🕒 {datetime.now().strftime('%Y-%m-%d')}"
      )
      print(msg)
      send_alert_once(sent_alerts, session_date, f"{ticker}:{result}", msg)
    elif price is None:
      fail_count += 1

    ticker_elapsed = time.time() - ticker_start
    total_elapsed = time.time() - start_time
    if price is not None:
      print(
          f"[{i + 1}/{total}] {name} ({ticker}) ₩{price:,.0f} done. ⏱ Ticker: {ticker_elapsed:.2f}s | Total: {total_elapsed:.2f}s")
    else:
      print(
          f"[{i + 1}/{total}] {name} ({ticker}) (가격 정보 없음) done. ⏱ Ticker: {ticker_elapsed:.2f}s | Total: {total_elapsed:.2f}s")

  print(f"\n✅ All done in {time.time() - start_time:.2f} seconds.")
  print(f"❌ Failed tickers: {fail_count}")


def should_run_now(now=None):
  now = now or datetime.now()
  return (
      now.weekday() < 5 and  # 월(0) ~ 금(4)
      now.date() not in KRX_HOLIDAYS and  # 한국거래소 휴장일 제외
      9 <= now.hour < 16  # 오전 9시 ~ 오후 3:59까지
  )


# ===== 메인 루프 =====
if __name__ == "__main__":
  # Start Heartbeat thread
  start_heartbeat(heartbeat_interval=3600)  # Send Heartbeat every 1 hour
  while True:
    if should_run_now():
      run_cross_check()
    time.sleep(600)  # 10분(600초) 대기
