# golden-dead-cross

[![Python](https://img.shields.io/badge/Python-3.11%2B-3776AB?logo=python&logoColor=white)](https://www.python.org)
[![yfinance](https://img.shields.io/badge/yfinance-410093)](https://pypi.org/project/yfinance/)
[![pykrx](https://img.shields.io/badge/pykrx-0A5BAA)](https://github.com/sharebook-kr/pykrx)
[![Telegram](https://img.shields.io/badge/Telegram-Bot-26A5E4?logo=telegram&logoColor=white)](https://core.telegram.org/bots)

KOSPI 200과 S&P 500 종목의 **골든크로스 / 데드크로스**(5일 이동평균선 × 20일 이동평균선)를 장중에 주기적으로 점검하고, 신호가 발생하면 텔레그램으로 알림을 보내는 스크립트입니다.

| 스크립트 | 대상 | 데이터 소스 | 점검 시간 (평일) |
| --- | --- | --- | --- |
| `kospi.py` | KOSPI 200 (코드에 하드코딩된 종목 목록) | [pykrx](https://github.com/sharebook-kr/pykrx) | 09:00 ~ 15:59 (서버 로컬 시간) |
| `snp500.py` | S&P 500 (Wikipedia에서 종목 목록 조회) | [yfinance](https://github.com/ranaroussi/yfinance) | 뉴욕 시간 09:30 ~ 16:00 (KST 22:30 ~ 05:00, 서머타임 해제 시 23:30 ~ 06:00) |

## 동작 방식

1. 10분마다 현재 시간이 점검 시간인지 확인합니다.
2. 점검 시간이면 모든 종목의 일봉 데이터를 받아 SMA5와 SMA20을 계산합니다.
3. 전일과 당일 사이에 두 이동평균선의 위아래가 바뀌면 신호로 판단합니다.
   - **골든크로스**: SMA5가 SMA20을 아래에서 위로 돌파
   - **데드크로스**: SMA5가 SMA20을 위에서 아래로 돌파
4. 신호가 발생한 종목마다 텔레그램 메시지를 보냅니다. 같은 날 같은 종목·신호는 한 번만 보냅니다. (`snp500.py`는 새로 알린 신호가 있으면 점검이 끝난 뒤 요약 메시지도 보냅니다.)
5. 별도 스레드에서 1시간마다 heartbeat 메시지를 보내 프로세스가 살아 있는지 알려줍니다.

> 두 스크립트 모두 [holidays](https://pypi.org/project/holidays/) 패키지의 거래소 휴장일(`kospi.py`는 한국거래소, `snp500.py`는 NYSE)에는 점검하지 않습니다. `kospi.py`는 서버 로컬 시간으로 판단하므로 서버 시간대가 KST여야 합니다. `snp500.py`는 뉴욕 시간으로 바꿔서 판단하므로 서버 시간대와 상관없이 서머타임이 반영됩니다.

## 요구 사항

- Python 3.11 이상 (`requirements.txt`의 numpy 2.3이 3.11 이상을 요구합니다)
- 텔레그램 봇 토큰과 알림을 받을 채팅 ID

## 설치

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## 텔레그램 봇 준비

1. 텔레그램에서 [@BotFather](https://t.me/BotFather)에게 `/newbot`을 보내 봇을 만들고 토큰을 받습니다.
2. 만든 봇에게 아무 메시지나 보내거나, 봇을 알림 받을 그룹에 초대합니다.
3. `https://api.telegram.org/bot<토큰>/getUpdates`를 열어 응답의 `message.chat.id` 값을 확인합니다. 이 값이 채팅 ID입니다.

두 스크립트에 같은 봇과 채팅을 써도 되고, 따로 만들어도 됩니다.

## 환경 변수

텔레그램 봇 토큰과 채팅 ID를 스크립트별로 설정합니다.

```bash
# KOSPI 200
export KOSPI_GOLDEN_DEAD_CROSS_TELEGRAM_BOT_TOKEN=...
export KOSPI_GOLDEN_DEAD_CROSS_TELEGRAM_CHAT_ID=...

# S&P 500
export SNP500_GOLDEN_DEAD_CROSS_TELEGRAM_BOT_TOKEN=...
export SNP500_GOLDEN_DEAD_CROSS_TELEGRAM_CHAT_ID=...
```

## 실행

포그라운드 실행:

```bash
python3 kospi.py
python3 snp500.py
```

백그라운드 실행:

```bash
mkdir -p output_files/logs
nohup python3 kospi.py > output_files/logs/kospi_nohup.out 2>&1 &
nohup python3 snp500.py > output_files/logs/snp500_nohup.out 2>&1 &
```

### 종료

```bash
pgrep -fl "kospi.py|snp500.py"   # PID 확인
kill -INT <PID>
```

`snp500.py`는 `Ctrl+C`나 `kill -INT`로 종료하면 텔레그램으로 중단 메시지를 보냅니다. 그냥 `kill`(SIGTERM)로 종료하면 메시지 없이 끝납니다.

## 알림 예시

`snp500.py`:

```
📈 AAPL (Apple Inc.)
➡️ Golden Cross 발생
💰 현재가: $230.15
🕒 2026-10-21 23:40
```

`kospi.py`:

```
📈 삼성전자 (005930) has a Golden Cross signal.
🕒 2026-10-21
```

이 밖에 `snp500.py`는 시작·중단·오류 메시지와, 새로 알린 신호가 있는 점검에 한해 요약(골든/데드크로스 전체·신규 개수, 실패 개수, 소요 시간)을 보내고, 두 스크립트 모두 1시간마다 heartbeat 메시지를 보냅니다.

## 종목 목록

- **KOSPI 200**: `kospi.py`의 `get_kospi200_tickers()` 안에 `종목명 , 종목코드` 형식으로 200개가 적혀 있습니다. 지수 구성 종목이 바뀌면 이 목록을 직접 고쳐야 합니다.
- **S&P 500**: 점검할 때마다 [Wikipedia 목록](https://en.wikipedia.org/wiki/List_of_S%26P_500_companies)에서 가져오므로 따로 관리할 필요가 없습니다. `BRK.B` 같은 종목은 yfinance 형식(`BRK-B`)으로 바꿔서 조회합니다.

## 로그 파일

| 파일 | 내용 |
| --- | --- |
| `snp500_monitor.log` | `snp500.py` 실행 로그 |
| `snp500_error.log` | `snp500.py` 메인 루프 오류 |
| `failed_tickers.log` | S&P 500 데이터 조회 실패 종목 |
| `failed_kospi_tickers.log` | KOSPI 데이터 조회 실패 종목 |
| `snp500_sent_alerts.json`, `kospi_sent_alerts.json` | 당일 이미 보낸 알림 기록 (중복 전송 방지용, 날짜가 바뀌면 새로 시작) |

`kospi.py`는 로그를 파일에 남기지 않고 표준 출력으로만 출력합니다.

## 주의 사항

- **장중 신호는 확정이 아닙니다.** 당일 일봉은 아직 진행 중이라 현재가로 계산합니다. 장중에 났던 신호가 종가 기준으로는 사라질 수 있습니다.
- **갑자기 정해진 임시 휴장일은 패키지를 갱신해야 반영됩니다.** 휴장일 달력은 `holidays` 패키지에 들어 있으므로, 임시 공휴일 등이 새로 지정되면 `pip install -U holidays`로 갱신하고 스크립트를 다시 시작해야 합니다.
- **미국 조기 폐장일은 반영하지 않습니다.** 추수감사절 다음 날 등 13:00에 장이 끝나는 날에도 16:00까지 점검합니다. 장이 끝난 뒤라 결과는 바뀌지 않고, 이미 보낸 알림은 다시 오지 않습니다.
- **`kospi.py`는 1년 치 데이터가 200거래일 이상인 종목만 점검합니다.** 상장한 지 1년이 안 된 종목은 조회 실패로 처리됩니다.
- 이 스크립트의 알림은 투자 조언이 아닙니다.

## requirements.txt 갱신

```bash
pip freeze > requirements.txt
```
