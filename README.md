[![Python](https://img.shields.io/badge/Python-3-3776AB?logo=python&logoColor=white)](https://www.python.org)
[![yfinance](https://img.shields.io/badge/yfinance-410093)](https://pypi.org/project/yfinance/)
[![pykrx](https://img.shields.io/badge/pykrx-0A5BAA)](https://github.com/sharebook-kr/pykrx)
[![Telegram](https://img.shields.io/badge/Telegram-Bot-26A5E4?logo=telegram&logoColor=white)](https://core.telegram.org/bots)

# 가상환경 구성
```
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

# requirements.txt 만드려면
```
pip freeze > requirements.txt
```

```
nohup python3 kospi.py > output_files/logs/nohup.out 2>&1 &

nohup python3 snp500.py > output_files/logs/nohup.out 2>&1 &

```
