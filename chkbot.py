import streamlit as st
import yfinance as yf
import pandas as pd

# 페이지 설정
st.set_page_config(page_title="Chkbot - 퀀트 주식 검증기", layout="centered", page_icon="📈")

# 타이틀 및 소개
st.title("📈 Chkbot: 퀀트 주식 적합도 검증기")
st.caption("거시경제(Macro) + 섹터(Sector) + 펀더멘털(Value) + 기술적 타이밍(Chart)")

symbol = st.text_input("종목코드(005930) 또는 미국 티커(AAPL, NVDA, QCOM 등) 입력:", value="AAPL")

def calculate_rsi(series, period=14):
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / (loss + 1e-9)
    return 100 - (100 / (1 + rs))

if st.button("Chkbot 분석 실행", type="primary"):
    with st.spinner("Chkbot이 시장 데이터 및 밸류에이션을 분석 중입니다..."):
        query = f"{symbol}.KS" if (symbol.isdigit() and len(symbol) == 6) else symbol.upper()
        ticker = yf.Ticker(query)
        hist = ticker.history(period="1y")
        
        if hist.empty and query.endswith(".KS"):
            query = query.replace(".KS", ".KQ")
            ticker = yf.Ticker(query)
            hist = ticker.history(period="1y")

        if hist.empty:
            st.error("종목 데이터를 불러올 수 없습니다. 티커나 종목번호를 다시 확인해주세요.")
        else:
            info = ticker.info
            name = info.get("shortName", symbol)
            sector = info.get("sector", "기타")
            price = hist['Close'].iloc[-1]
            ma_200 = hist['Close'].rolling(200).mean().iloc[-1]
            rsi = calculate_rsi(hist['Close']).iloc[-1]
            peg = info.get("pegRatio")
            rev_growth = info.get("revenueGrowth")

            # 1. 매크로 점수 (미 10년물 국채 금리) - 20점 만점
            tnx = yf.Ticker("^TNX").history(period="1mo")
            macro_score = 15
            macro_text = "보통 수준"
            if not tnx.empty:
                yield_val = tnx['Close'].iloc[-1]
                if yield_val < 4.2:
                    macro_score = 20
                    macro_text = f"우호적 ({yield_val:.2f}%)"
                else:
                    macro_text = f"경계 ({yield_val:.2f}%)"

            # 2. 펀더멘털 점수 (PEG 및 매출 성장률) - 40점 만점
            fund_score = 0
            if peg and 0 < peg <= 1.5:
                fund_score += 25
            elif not peg:
                fund_score += 15

            if rev_growth and rev_growth > 0.15:
                fund_score += 15
            elif rev_growth and rev_growth > 0:
                fund_score += 8

            # 3. 기술적 추세 점수 (200일선 및 RSI) - 20점 만점
            tech_score = 0
            if price > ma_200:
                tech_score += 10
            if 35 <= rsi <= 55:
                tech_score += 10
            else:
                tech_score += 5

            # 4. 섹터 기본 점수 (20점 만점)
            sector_score = 20

            total_score = macro_score + fund_score + tech_score + sector_score

            st.divider()
            st.subheader(f"{name} ({symbol.upper()})")
            st.write(f"**섹터:** {sector} | **현재가:** {price:,.2f}")

            # 요약 지표 카드
            col1, col2, col3 = st.columns(3)
            col1.metric("거시 환경", macro_text)
            col2.metric("RSI(14)", f"{rsi:.1f}")
            col3.metric("Chkbot 종합 점수", f"{total_score} / 100")

            st.progress(total_score / 100)

            # 판정 메시지
            if total_score >= 75:
                st.success("🟢 Chkbot 판정: 적극 매수 고려 (성장성, 추세, 매크로 삼박자 우수)")
            elif total_score >= 50:
                st.warning("🟡 Chkbot 판정: 분할 매수 / 관망 (일부 밸류 또는 추세 지표 확인 필요)")
            else:
                st.error("🔴 Chkbot 판정: 매수 보류 (역배열 하락 또는 성장 둔화 리스크)")

            # 주가 차트
            st.write("📈 **최근 1개년 주가 추세**")
            st.line_chart(hist['Close'])
