import streamlit as st
import yfinance as yf
import pandas as pd
import datetime

# 페이지 기본 설정 (탭 제목, 아이콘)
st.set_page_config(page_title="US Stock Dashboard", page_icon="📈")

# --- 사이드바 (입력 패널) ---
st.sidebar.header("🔍 종목 검색")
ticker_input = st.sidebar.text_input("티커 입력 (예: AAPL, TSLA)", value="AAPL").upper()
period = st.sidebar.selectbox("조회 기간", ["1mo", "3mo", "6mo", "1y", "5y", "max"], index=2)

# --- 메인 화면 ---
st.title(f"🇺🇸 {ticker_input} 주식 분석 대시보드")

if ticker_input:
    try:
        # 데이터 로딩
        with st.spinner('데이터를 가져오는 중입니다...'):
            stock = yf.Ticker(ticker_input)
            hist = stock.history(period=period)
            info = stock.info

        if hist.empty:
            st.error("데이터가 없습니다. 티커를 확인해주세요.")
        else:
            # 1. 요약 정보 표시
            col1, col2, col3 = st.columns(3)
            current_price = hist['Close'].iloc[-1]
            prev_price = hist['Close'].iloc[-2]
            diff = current_price - prev_price
            diff_pct = (diff / prev_price) * 100
            
            with col1:
                st.metric("현재 주가", f"${current_price:.2f}", f"{diff:.2f} ({diff_pct:.2f}%)")
            with col2:
                # 안전하게 데이터 가져오기 (없으면 'N/A')
                per = info.get('trailingPE', 'N/A')
                st.metric("PER (주가수익비율)", f"{per}")
            with col3:
                high_52 = info.get('fiftyTwoWeekHigh', 0)
                st.metric("52주 최고가", f"${high_52}")

            # 2. 메인 차트
            st.subheader("📈 주가 추이 (Close Price)")
            st.line_chart(hist['Close'])

            # 3. 데이터프레임 (테이블)
            with st.expander("상세 데이터 보기"):
                st.dataframe(hist.sort_index(ascending=False))

    except Exception as e:
        st.error(f"오류가 발생했습니다: {e}")
