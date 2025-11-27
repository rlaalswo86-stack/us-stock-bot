import yfinance as yf
import pandas as pd
import requests
import os
import time

# ---------------------------------------------------------
# [Setup] 환경 변수 (Secrets)
# ---------------------------------------------------------
TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN')
CHAT_ID = os.environ.get('CHAT_ID')

# ---------------------------------------------------------
# [Function 1] S&P 500 종목 리스트 가져오기 (Data Acquisition)
# ---------------------------------------------------------
def get_sp500_tickers():
    """위키피디아에서 S&P 500 종목 리스트를 크롤링합니다."""
    url = 'https://en.wikipedia.org/wiki/List_of_S%26P_500_companies'
    try:
        # pandas의 read_html 기능으로 웹페이지의 표를 통째로 가져옵니다.
        tables = pd.read_html(url)
        df = tables[0] # 첫 번째 표가 종목 리스트입니다.
        
        # 기호 수정: 위키는 'BRK.B'로 쓰지만 야후는 'BRK-B'로 씁니다.
        tickers = df['Symbol'].apply(lambda x: x.replace('.', '-')).tolist()
        print(f"S&P 500 리스트 확보 완료: 총 {len(tickers)}개 종목")
        return tickers
    except Exception as e:
        print(f"리스트 확보 실패: {e}")
        # 실패 시 비상용으로 주요 종목만 반환 (Fail-safe)
        return ['AAPL', 'MSFT', 'GOOGL', 'NVDA', 'TSLA']

# ---------------------------------------------------------
# [Function 2] 텔레그램 전송 (Transmitter)
# ---------------------------------------------------------
def send_telegram_message(message):
    if not TELEGRAM_TOKEN or not CHAT_ID:
        print(f"[전송 불가] 토큰 없음. 내용:\n{message}")
        return

    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    # 메시지가 너무 길면 잘릴 수 있어서 나눠서 보낼 수도 있지만, 여기선 1차 필터링만 합니다.
    data = {'chat_id': CHAT_ID, 'text': message}
    requests.post(url, data=data)

# ---------------------------------------------------------
# [Function 3] 지표 계산 (DSP Unit)
# ---------------------------------------------------------
def calculate_rsi(data, window=14):
    delta = data['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

# ---------------------------------------------------------
# [Main Loop] 메인 분석 로직
# ---------------------------------------------------------
def run_analysis():
    # 1. 대상 종목 가져오기
    tickers = get_sp500_tickers()
    
    print(f"시스템 가동... 총 {len(tickers)}개 종목 전수 검사 시작")
    picked_stocks = []
    
    # 카운터 (진행 상황 표시용)
    count = 0
    
    for ticker in tickers:
        count += 1
        # 로그가 너무 많이 찍히면 지저분하니 50개마다 생존신호 출력
        if count % 50 == 0:
            print(f"[{count}/{len(tickers)}] 진행 중...")

        try:
            stock = yf.Ticker(ticker)
            hist = stock.history(period="6mo")
            
            if hist.empty: continue

            # --- [지표 계산] ---
            current_price = hist['Close'].iloc[-1]
            ma_20 = hist['Close'].rolling(window=20).mean().iloc[-1]
            hist['RSI'] = calculate_rsi(hist)
            current_rsi = hist['RSI'].iloc[-1]
            
            # API 호출 최소화를 위해 info는 꼭 필요할 때만 부르거나, 
            # 대량 처리시에는 속도를 위해 생략하기도 합니다. 
            # 여기서는 정밀 분석을 위해 호출하되, 에러나면 넘어갑니다.
            try:
                info = stock.info
                per = info.get('trailingPE', 999)
                roe = info.get('returnOnEquity', 0)
                pbr = info.get('priceToBook', 999)
            except:
                per, roe, pbr = 999, 0, 999 # 기본값 설정
            
            # --- [필터링 조건 (Threshold)] ---
            # 조건이 너무 약하면 알림 폭탄을 맞습니다. 조건을 조금 빡빡하게 조이겠습니다.
            cond_per = (per < 30) and (per > 0) # PER 30이하 (적자 기업 제외)
            cond_roe = roe > 0.15               # ROE 15% 이상 (우량주)
            cond_rsi = current_rsi < 35         # RSI 35 미만 (과매도 강력 신호)
            
            # (옵션) 20일 이평선보다는 아래에 있어야 '저점 매수'겠죠?
            # cond_ma = current_price < ma_20 

            if cond_per and cond_roe and cond_rsi:
                status_msg = (
                    f"💎 {ticker} 발굴!\n"
                    f"P:${current_price:.1f} / RSI:{current_rsi:.1f}\n"
                    f"PER:{per:.1f} / ROE:{roe*100:.1f}%"
                )
                picked_stocks.append(status_msg)
                print(f"--> {ticker} 조건 만족!")

        except Exception as e:
            # 개별 종목 에러는 무시하고 계속 진행 (Watchdog)
            continue
            
    # 결과 보고
    if picked_stocks:
        header = f"📊 [S&P 500 전수 조사 결과]\n총 {len(picked_stocks)}개 포착됨\n\n"
        full_msg = header + "\n\n".join(picked_stocks)
        
        # 텔레그램 메시지 길이 제한(4096자) 방지: 너무 길면 잘라서 보냄
        if len(full_msg) > 4000:
            send_telegram_message(header + "종목이 너무 많아 상위 10개만 보냅니다.")
            send_telegram_message("\n\n".join(picked_stocks[:10]))
        else:
            send_telegram_message(full_msg)
    else:
        print("조건에 맞는 종목 없음.")
        send_telegram_message("오늘은 매수 추천 종목이 없습니다. (Relax Mode)")

if __name__ == "__main__":
    run_analysis()
