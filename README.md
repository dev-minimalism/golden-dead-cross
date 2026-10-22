# golden-dead-cross

[![Python](https://img.shields.io/badge/Python-3-3776AB?logo=python&logoColor=white)](https://www.python.org)
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
4. 신호가 발생한 종목마다 텔레그램 메시지를 보냅니다. (`snp500.py`는 점검이 끝나면 요약 메시지도 보냅니다.)
5. 별도 스레드에서 1시간마다 heartbeat 메시지를 보내 프로세스가 살아 있는지 알려줍니다.

> `kospi.py`는 서버 로컬 시간으로 판단하므로 서버 시간대가 KST여야 합니다. `snp500.py`는 뉴욕 시간으로 바꿔서 판단하므로 서버 시간대와 상관없이 서머타임이 반영됩니다. 미국 공휴일은 따로 거르지 않습니다.

## 설치

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

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

## 로그 파일

| 파일 | 내용 |
| --- | --- |
| `snp500_monitor.log` | `snp500.py` 실행 로그 |
| `snp500_error.log` | `snp500.py` 메인 루프 오류 |
| `failed_tickers.log` | S&P 500 데이터 조회 실패 종목 |
| `failed_kospi_tickers.log` | KOSPI 데이터 조회 실패 종목 |

`kospi.py`는 로그를 파일에 남기지 않고 표준 출력으로만 출력합니다.

## requirements.txt 갱신

```bash
pip freeze > requirements.txt
```
