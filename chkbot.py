import streamlit as st
import yfinance as yf
import pandas as pd

st.set_page_config(page_title="Chkbot v4 - 무결점 안정화", layout="centered", page_icon="🔮")

st.title("🔮 Chkbot v4: 프로 퀀트 주식 검증기")
st.caption("시스템 멈춤 방지 및 안전성 강화 버전")

symbol = st.text_input("종목코드(005930) 또는 미국 티커(AAPL, MXL 등) 입력:", value="MXL").strip()

def calculate_rsi(series, period=14):
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / (loss + 1e-9)
    return 100 - (100 / (1 + rs))

if st.button("Chkbot 정밀 분석 실행", type="primary"):
    with st.spinner("야후 파이낸스에서 데이터를 안전하게 가져오는 중입니다..."):
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
                sector = info.get("sector", "기타")
                
                price = float(hist['Close'].iloc[-1])
                ma_200 = float(hist['Close'].rolling(200).mean().iloc[-1])
                
                try:
                    rsi = float(calculate_rsi(hist['Close']).iloc[-1])
                except:
                    rsi = 50.0 

                current_volume = float(hist['Volume'].iloc[-1])
                avg_volume_10d = float(hist['Volume'].tail(10).mean())

                forward_pe = info.get("forwardPE")
                trailing_pe = info.get("trailingPE")
                pb_ratio = info.get("priceToBook")
                profit_margin = info.get("profitMargins")

                score_details = {}

                value_score = 0
                value_notes = []
                if sector == "Financial Services":
                    if pb_ratio is not None:
                        if pb_ratio < 1.0:
                            value_score, value_notes = 40, [f"절대적 저평가(P/B {pb_ratio:.2f})"]
                        elif pb_ratio < 1.5:
                            value
