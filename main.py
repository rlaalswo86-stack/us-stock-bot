import yfinance as yf
import pandas as pd
import requests
import os

# ---------------------------------------------------------
# [Setup] 환경 변수 및 설정 (Secrets & Config)
# ---------------------------------------------------------
# GitHub Secrets에 등록된 키를 가져옵니다. (보안 구역)
TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN')
CHAT_ID = os.environ.get('CHAT_ID')

# 분석할 종목 리스트 (관심 종목)
TARGET_TICKERS = [
    'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'TSLA', 'META',
    'AMD', 'INTC', 'QCOM', 'KO', 'MCD', 'O'
]

# ---------------------------------------------------------
# [Function 1] 텔레그램 전송 함수 (Transmitter)
# ---------------------------------------------------------
def send_telegram_message(message):
    if not TELEGRAM_TOKEN or not CHAT_ID:
        print("Error: 텔레그램 토큰이 없습니다. (Local Test Mode)")
        print(f"[메시지 미리보기]\n{message}")
        return

    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data = {'chat_id': CHAT_ID, 'text': message}
    try:
        requests.post(url, data=data)
    except Exception as e:
        print(f"전송 실패: {e}")

# ---------------------------------------------------------
# [Function 2] RSI 계산 (DSP Logic)
# ---------------------------------------------------------
def calculate_rsi(data, window=14):
    delta = data['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

# ---------------------------------------------------------
# [Main Loop] 분석 및 알림 (Analysis & Alert)
# ---------------------------------------------------------
def run_analysis():
    print("시스템 가동... 분석 시작")
    picked_stocks = []

    for ticker in TARGET_TICKERS:
        try:
            stock = yf.Ticker(ticker)
            # 6mo 수정 완료!
            hist = stock.history(period="6mo")
            info = stock.info
            
            if hist.empty: continue

            # 데이터 가공
            current_price = hist['Close'].iloc[-1]
            ma_20 = hist['Close'].rolling(window=20).mean().iloc[-1]
            hist['RSI'] = calculate_rsi(hist)
            current_rsi = hist['RSI'].iloc[-1]
            
            per = info.get('trailingPE', 999)
            roe = info.get('returnOnEquity', 0)

            # 필터링 조건 (Threshold)
            cond_per = per < 40
            cond_roe = roe > 0.1
            cond_rsi = current_rsi < 70
            cond_ma = current_price > ma_20

            # 모든 조건 만족 시(AND Gate)
            if cond_per and cond_roe and cond_rsi: # cond_ma 등은 취향껏 추가
                signal = (
                    f"🚀 {ticker} 포착!\n"
                    f"- 가격: ${current_price:.2f}\n"
                    f"- PER: {per:.2f}\n"
                    f"- RSI: {current_rsi:.2f}\n"
                    f"- ROE: {roe*100:.2f}%"
                )
                picked_stocks.append(signal)

        except Exception as e:
            print(f"Skip {ticker}: {e}")
            continue

    # 결과 전송
    if picked_stocks:
        final_msg = f"[오늘의 미국 주식 추천]\n총 {len(picked_stocks)}개 발견\n\n" + "\n\n".join(picked_stocks)
        send_telegram_message(final_msg)
    else:
        print("조건에 맞는 종목이 없습니다.")
        # 필요하다면 "오늘 쉴 종목 없음" 메시지를 보내도 됩니다.

if __name__ == "__main__":
    run_analysis()