import streamlit as st
import yfinance as yf
import pandas as pd

st.set_page_config(page_title="US Stock", page_icon="📈")

st.sidebar.header("🔍 종목 검색")
ticker_input = st.sidebar.text_input("티커 입력 (예: AAPL, TSLA)", value="AAPL").upper()
period = st.sidebar.selectbox("조회 기간", ["1mo", "3mo", "6mo", "1y", "5y", "max"], index=2)

st.title(f"🇺🇸 {ticker_input} 주식 분석")

if ticker_input:
    try:
        with st.spinner('데이터 수신 중...'):
            stock = yf.Ticker(ticker_input)
            hist = stock.history(period=period)
            info = stock.info

        if hist.empty:
            st.error("데이터가 없습니다.")
        else:
            col1, col2 = st.columns(2)
            current_price = hist['Close'].iloc[-1]
            prev_price = hist['Close'].iloc[-2]
            delta = current_price - prev_price
            
            with col1:
                st.metric("현재 주가", f"${current_price:.2f}", f"{delta:.2f}")
            with col2:
                per = info.get('trailingPE', 'N/A')
                st.metric("PER", f"{per}")

            st.line_chart(hist['Close'])
            
            with st.expander("상세 데이터"):
                st.dataframe(hist.sort_index(ascending=False))

    except Exception as e:
        st.error(f"에러: {e}")
