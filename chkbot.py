import streamlit as st
import yfinance as yf
import pandas as pd

st.set_page_config(page_title="Chkbot v4 - 무결점 안정화", layout="centered", page_icon="🔮")

st.title("🔮 Chkbot v4: 프로 퀀트 주식 검증기")
st.caption("시스템 멈춤 방지 및 안전성 강화 버전")

# 입력창 공백 자동 제거 추가
symbol = st.text_input("종목코드(005930) 또는 미국 티커(AAPL, MXL 등) 입력:", value="MXL").strip()

def calculate_rsi(series, period=14):
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / (loss + 1e-9)
    return 100 - (100 / (1 + rs))

if st.button("Chkbot 정밀 분석 실행", type="primary"):
    with st.spinner("야후 파이낸스에서 데이터를 안전하게 가져오는 중입니다..."):
        # 전체 로직을 try-except로 감싸서 앱이 먹통이 되는 것을 방지
        try:
            is_korean = symbol.isdigit() and len(symbol) == 6
            query = f"{symbol}.KS" if is_korean else symbol.upper()
            
            ticker = yf.Ticker(query)
            hist = ticker.history(period="1y")
            
            if hist.empty and is_korean:
                query = symbol + ".KQ"
                ticker = yf.Ticker(query)
                hist = ticker.history(period="1y")

            if hist.empty:
                st.error("해당 종목의 데이터를 불러올 수 없습니다. 티커를 다시 확인해 주세요.")
            else:
                info = ticker.info
                name = info.get("shortName", symbol)
                sector = info.get("sector", "기타
