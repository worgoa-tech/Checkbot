import streamlit as st
import yfinance as yf
import pandas as pd

st.set_page_config(page_title="Chkbot v3.1 - 프로 퀀트 검증기", layout="centered", page_icon="🔮")

st.title("🔮 Chkbot v3.1: 프로 퀀트 주식 검증기")
st.caption("미래 실적(Forward) + 섹터별 맞춤 평가 + 거래량 수급 + 결측치 예외 처리 완료")

symbol = st.text_input("종목코드(005930) 또는 미국 티커(AAPL, MXL 등) 입력:", value="MXL")

def calculate_rsi(series, period=14):
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / (loss + 1e-9)
    return 100 - (100 / (1 + rs))

if st.button("Chkbot 정밀 분석 실행", type="primary"):
    with st.spinner("미래 실적 전망치와 섹터 데이터를 분석 중입니다..."):
        is_korean = symbol.isdigit() and len(symbol) == 6
        query = f"{symbol}.KS" if is_korean else symbol.upper()
        ticker = yf.Ticker(query)
        hist = ticker.history(period="1y")
        
        if hist.empty and query.endswith(".KS"):
            query = query.replace(".KS", ".KQ")
            ticker = yf.Ticker(query)
            hist = ticker.history(period="1y")

        if hist.empty:
            st.error("종목 데이터를 불러올 수 없습니다.")
        else:
            info = ticker.info
            name = info.get("shortName", symbol)
            sector = info.get("sector", "기타")
            
            price = hist['Close'].iloc[-1]
            ma_200 = hist['Close'].rolling(200).mean().iloc[-1]
            rsi = calculate_rsi(hist['Close']).iloc[-1]
            
            # 수급(거래량) 지표
            current_volume = hist['Volume'].iloc[-1]
            avg_volume_10d = hist['Volume'].tail(10).mean()

            # 가치 평가 지표
            forward_pe = info.get("forwardPE")
            trailing_pe = info.get("trailingPE")
            pb_ratio = info.get("priceToBook")
            profit_margin = info.get("profitMargins")

            score_details = {}

            # ----------------------------------------------------
            # 1. 밸류에이션 및 미래 성장성 (섹터별 맞춤) - 40점 만점
            # ----------------------------------------------------
            value_score = 0
            value_notes = []

            # 금융 섹터는 PBR 위주로 평가
            if sector == "Financial Services":
                if pb_ratio is not None:
                    if pb_ratio < 1.0:
                        value_score += 40
                        value_notes.append(f"절대적 저평가(P/B {pb_ratio:.2f})")
                    elif pb_ratio < 1.5:
                        value_score += 25
                        value_notes.append(f"적정 수준(P/B {pb_ratio:.2f})")
                    else:
                        value_score += 10
                        value_notes.append(f"다소 고평가(P/B {pb_ratio:.2f})")
                else:
                    value_notes.append("PBR 데이터 누락 (0점)")
            
