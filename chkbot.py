import streamlit as st
import yfinance as yf
import pandas as pd

st.set_page_config(page_title="Chkbot", layout="centered", page_icon="🔮")
st.title("🔮 Chkbot: 프로 퀀트 주식 검증기")

symbol = st.text_input("종목코드(005930) 또는 미국 티커(AAPL, MXL):", value="MXL").strip()

if st.button("Chkbot 분석 실행", type="primary"):
    with st.spinner("데이터 분석 중..."):
        query = f"{symbol}.KS" if (symbol.isdigit() and len(symbol) == 6) else symbol.upper()
        ticker = yf.Ticker(query)
        hist = ticker.history(period="1y")

        if hist.empty and symbol.isdigit():
            query = f"{symbol}.KQ"
            ticker = yf.Ticker(query)
            hist = ticker.history(period="1y")

        if hist.empty:
            st.error("종목 데이터를 불러올 수 없습니다.")
        else:
            info = ticker.info
            price = float(hist['Close'].iloc[-1])
            ma200 = float(hist['Close'].rolling(200).mean().iloc[-1])
            f_pe, t_pe = info.get("forwardPE"), info.get("trailingPE")
            pm = info.get("profitMargins")
            vol_cur, vol_avg = float(hist['Volume'].iloc[-1]), float(hist['Volume'].tail(10).mean())

            # 1. 밸류에이션 (40점)
            val_sc, val_msg = 0, "추정치 부족/적자 (0점)"
            if f_pe is not None:
                if t_pe is not None and f_pe < t_pe: val_sc, val_msg = 40, f"내년 실적 개선 (FWD PE {f_pe:.1f})"
                elif f_pe < 25: val_sc, val_msg = 25, f"적정 밸류 (FWD PE {f_pe:.1f})"
                else: val_sc, val_msg = 10, f"고평가/성장 둔화 (FWD PE {f_pe:.1f})"
            elif t_pe is not None:
                val_sc, val_msg = (15, f"과거 실적 저평가 ({t_pe:.1f})") if t_pe < 20 else (5, f"과거 실적 고평가 ({t_pe:.1f})")

            # 2. 흑자 마진 (20점)
            mag_sc = 20 if (pm and pm > 0.15) else (10 if (pm and pm > 0) else 0)

            # 3. 기술적 추세 (25점)
            tech_sc = 15 if price > ma200 else 0

            # 4. 수급 (15점)
            vol_sc = 15 if (vol_avg > 0 and vol_cur > vol_avg * 1.2) else (10 if vol_cur > vol_avg else 5)

            total = val_sc + mag_sc + tech_sc + vol_sc

            st.divider()
            st.subheader(f"{info.get('shortName', symbol)} ({symbol.upper()})")
            st.metric("종합 점수", f"{total} / 100")
            st.progress(min(max(total, 0), 100) / 100)
            st.write(f"- **가치평가**: `{val_sc}/40점` ({val_msg})")
            st.write(f"- **마진/수익**: `{mag_sc}/20점` (순이익률: {pm*100:.1f}%" if pm else "- **마진/수익**: `0/20점` (데이터 없음)")
            st.write(f"- **200일선 추세**: `{tech_sc}/25점` ({'상승 정배열' if tech_sc else '하락 역배열'})")
            st.write(f"- **거래량 수급**: `{vol_sc}/15점`")
            st.line_chart(hist['Close'])
