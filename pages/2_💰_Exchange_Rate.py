import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup

st.set_page_config(page_title="Exchange Rate", page_icon="💰")

st.title("💰 실시간 환율 (Naver Finance)")

def get_exchange_rate(target="USD"):
    url = "https://finance.naver.com/marketindex/"
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")
    
    # 네이버 금융 시장지표 selector
    data = soup.select("div.head_info")
    
    rates = {}
    # 0: USD, 1: JPY, 2: EUR, 3: CNY
    # 태국 바트는 메인에 안 나올 수 있어서 별도 처리 필요하지만, 일단 주요 통화부터
    
    try:
        usd = data[0].select_one("span.value").text.replace(",", "")
        rates['USD'] = float(usd)
        
        # 태국 바트(THB) 상세 페이지 크롤링
        url_thb = "https://finance.naver.com/marketindex/exchangeDetail.naver?marketindexCd=FX_THBKRW"
        res_thb = requests.get(url_thb)
        soup_thb = BeautifulSoup(res_thb.text, "html.parser")
        thb = soup_thb.select_one("div.head_info > span.value").text.replace(",", "")
        rates['THB'] = float(thb)
        
    except Exception as e:
        st.error(f"환율 정보를 가져오는데 실패했습니다: {e}")
        return None
        
    return rates

# --- UI 구성 ---
if st.button("환율 새로고침"):
    st.cache_data.clear() # 캐시 삭제 후 다시 로딩

rates = get_exchange_rate()

if rates:
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric(label="🇺🇸 미국 달러 (USD)", value=f"{rates['USD']} 원")
        
    with col2:
        st.metric(label="🇹🇭 태국 바트 (THB)", value=f"{rates['THB']} 원")
        
    st.info(f"💡 태국에서 100만원 살기 하려면? -> 약 {1000000 / rates['THB']:.0f} 바트 필요")
