import streamlit as st
import yfinance as yf
import pandas as pd

# 페이지 설정
st.set_page_config(page_title="Chkbot v2 - 정밀 퀀트 검증기", layout="centered", page_icon="🎯")

st.title("🎯 Chkbot v2: 정밀 퀀트 주식 검증기")
st.caption("결측치 페널티 + 순이익 흑자 검증 + 재무 건전성 + 동적 시장 모멘텀 반영")

symbol = st.text_input("종목코드(005930) 또는 미국 티커(AAPL, AEHR, NVDA 등) 입력:", value="AEHR")

def calculate_rsi(series, period=14):
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / (loss + 1e-9)
    return 100 - (100 / (1 + rs))

if st.button("Chkbot 정밀 분석 실행", type="primary"):
    with st.spinner("Chkbot이 재무 건전성 및 밸류에이션을 엄격하게 심사 중입니다..."):
        is_korean = symbol.isdigit() and len(symbol) == 6
        query = f"{symbol}.KS" if is_korean else symbol.upper()
        ticker = yf.Ticker(query)
        hist = ticker.history(period="1y")
        
        if hist.empty and query.endswith(".KS"):
            query = query.replace(".KS", ".KQ")
            ticker = yf.Ticker(query)
            hist = ticker.history(period="1y")

        if hist.empty:
            st.error("종목 데이터를 불러올 수 없습니다. 티커나 종목코드를 확인해주세요.")
        else:
            info = ticker.info
            name = info.get("shortName", symbol)
            sector = info.get("sector", "기타")
            price = hist['Close'].iloc[-1]
            ma_200 = hist['Close'].rolling(200).mean().iloc[-1]
            rsi = calculate_rsi(hist['Close']).iloc[-1]
            
            # 재무/밸류 지표 추출
            peg = info.get("pegRatio")
            rev_growth = info.get("revenueGrowth")
            profit_margin = info.get("profitMargins")
            debt_to_equity = info.get("debtToEquity")

            score_details = {}

            # ----------------------------------------------------
            # 1. 매크로 점수 (미 10년물 국채 금리) - 15점 만점
            # ----------------------------------------------------
            macro_score = 10
            macro_desc = "중립"
            try:
                tnx = yf.Ticker("^TNX").history(period="1mo")
                if not tnx.empty:
                    rate = tnx['Close'].iloc[-1]
                    if rate < 4.2:
                        macro_score = 15
                        macro_desc = f"우호적 ({rate:.2f}%)"
                    elif rate > 4.7:
                        macro_score = 5
                        macro_desc = f"고금리 부담 ({rate:.2f}%)"
                    else:
                        macro_desc = f"보통 ({rate:.2f}%)"
            except:
                macro_score = 10
            score_details["거시경제(금리)"] = (macro_score, 15, macro_desc)

            # ----------------------------------------------------
            # 2. 펀더멘털 & 흑자 건전성 - 45점 만점 (가장 엄격)
            # ----------------------------------------------------
            fund_score = 0
            fund_notes = []

            # (1) PEG 밸류에이션 (20점): 데이터 없으면 0점!
            if peg is not None:
                if 0 < peg <= 1.2:
                    fund_score += 20
                    fund_notes.append(f"초저평가성장(PEG {peg:.2f})")
                elif 1.2 < peg <= 2.0:
                    fund_score += 12
                    fund_notes.append(f"적정성장(PEG {peg:.2f})")
                else:
                    fund_score += 3
                    fund_notes.append(f"고평가부담(PEG {peg:.2f})")
            else:
                fund_score += 0
                fund_notes.append("PEG 추정불가(데이터누락/적자 - 0점)")

            # (2) 순이익 흑자 여부 (15점): 적자 기업 필터링 핵심!
            if profit_margin is not None:
                if profit_margin > 0.15:
                    fund_score += 15
                    fund_notes.append(f"고수익 흑자({profit_margin*100:.1f}%)")
                elif profit_margin > 0:
                    fund_score += 10
                    fund_notes.append(f"흑자 유지({profit_margin*100:.1f}%)")
                else:
                    fund_score += 0
                    fund_notes.append(f"영업적자/순손실({profit_margin*100:.1f}%)")
            else:
                fund_score += 0
                fund_notes.append("마진 데이터 미비(0점)")

            # (3) 매출 성장률 (10점)
            if rev_growth is not None:
                if rev_growth > 0.15:
                    fund_score += 10
                    fund_notes.append(f"매출고성장(+{rev_growth*100:.1f}%)")
                elif rev_growth > 0:
                    fund_score += 5
                    fund_notes.append(f"매출성장(+{rev_growth*100:.1f}%)")
                else:
                    fund_score += 0
                    fund_notes.append("매출 역성장")
            else:
                fund_score += 0

            score_details["펀더멘털/흑자"] = (fund_score, 45, ", ".join(fund_notes))

            # ----------------------------------------------------
            # 3. 기술적 추세 및 눌림목 타점 - 25점 만점
            # ----------------------------------------------------
            tech_score = 0
            tech_notes = []

            # (1) 200일선 정배열 (15점)
            if price > ma_200:
                tech_score += 15
                tech_notes.append("200일선 위 상승추세")
            else:
                tech_score += 0
                tech_notes.append("200일선 아래 역배열하락")

            # (2) RSI 눌림목 구간 (10점)
            if 40 <= rsi <= 55:
                tech_score += 10
                tech_notes.append(f"최적눌림목(RSI {rsi:.1f})")
            elif 30 <= rsi < 40 or 55 < rsi <= 65:
                tech_score += 6
                tech_notes.append(f"양호(RSI {rsi:.1f})")
            elif rsi > 70:
                tech_score += 2
                tech_notes.append(f"단기과열(RSI {rsi:.1f})")
            else:
                tech_score += 2
                tech_notes.append(f"침체(RSI {rsi:.1f})")

            score_details["차트/기술적"] = (tech_score, 25, ", ".join(tech_notes))

            # ----------------------------------------------------
            # 4. 시장/지수 모멘텀 (동적 체크) - 15점 만점
            # ----------------------------------------------------
            market_score = 8
            market_desc = "시장 보통"
            try:
                bench_ticker = "^KS11" if is_korean else "SPY"
                bench_hist = yf.Ticker(bench_ticker).history(period="1y")
                if not bench_hist.empty:
                    bench_close = bench_hist['Close'].iloc[-1]
                    bench_ma200 = bench_hist['Close'].rolling(200).mean().iloc[-1]
                    if bench_close > bench_ma200:
                        market_score = 15
                        market_desc = "대표 지수 상승장 우호"
                    else:
                        market_score = 5
                        market_desc = "대표 지수 하락장 경계"
            except:
                market_score = 8
            score_details["시장환경"] = (market_score, 15, market_desc)

            # ----------------------------------------------------
            # 총점 계산
            # ----------------------------------------------------
            total_score = macro_score + fund_score + tech_score + market_score

            st.divider()
            st.subheader(f"{name} ({symbol.upper()})")
            st.write(f"**섹터:** {sector} | **현재가:** {price:,.2f}")

            col1, col2, col3 = st.columns(3)
            col1.metric("종합 점수", f"{total_score} / 100")
            col2.metric("순이익률", f"{profit_margin*100:.1f}%" if profit_margin else "N/A")
            col3.metric("RSI(14)", f"{rsi:.1f}")

            st.progress(total_score / 100)

            # 세부 점수표 출력
            st.write("📋 **세부 팩터 채점 내역**")
            for factor, (sc, max_sc, desc) in score_details.items():
                st.markdown(f"- **{factor}**: `{sc}/{max_sc}점` ({desc})")

            # 최종 판정
            st.divider()
            if total_score >= 80:
                st.success("🟢 Chkbot 판정: 강력 매수 후보 (실적 흑자 + 추세 정배열 + 적정 밸류)")
            elif total_score >= 60:
                st.warning("🟡 Chkbot 판정: 분할 접근 / 관망 (성장성은 있으나 일부 지표 검토 필요)")
            else:
                st.error("🔴 Chkbot 판정: 매수 부적합 (적자, 결측치, 또는 하락 역배열 리스크)")

            st.write("📈 **최근 1개년 주가 추세 (파란선: 주가 / 주황선: 200일선)**")
            chart_df = pd.DataFrame({
                "현재가": hist['Close'],
                "200일선": hist['Close'].rolling(200).mean()
            })
            st.line_chart(chart_df)
