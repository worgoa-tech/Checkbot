import streamlit as st
import yfinance as yf
import pandas as pd

st.set_page_config(page_title="Chkbot v3 - 프로 퀀트 검증기", layout="centered", page_icon="🔮")

st.title("🔮 Chkbot v3: 프로 퀀트 주식 검증기")
st.caption("미래 실적(Forward) + 섹터별 맞춤 평가 + 거래량 수급 반영")

symbol = st.text_input("종목코드(005930) 또는 미국 티커(AAPL, JPM 등) 입력:", value="AAPL")

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
            
            # 일반 섹터는 미래 예상 PER(Forward P/E)로 평가
            else:
                if forward_pe and trailing_pe:
                    if forward_pe < trailing_pe:
                        value_score += 40
                        value_notes.append(f"미래 실적 성장 예상 (Forward PE {forward_pe:.1f})")
                    elif forward_pe < 25:
                        value_score += 25
                        value_notes.append(f"준수한 미래 밸류 (Forward PE {forward_pe:.1f})")
                    else:
                        value_score += 10
                        value_notes.append(f"미래 실적 둔화 우려/고평가 (Forward PE {forward_pe:.1f})")
                else:
                    value_notes.append("미래 추정치(Forward PE) 미비 (0점)")

            score_details["미래 가치평가"] = (value_score, 40, ", ".join(value_notes))

            # ----------------------------------------------------
            # 2. 흑자 마진 (안전마진) - 20점 만점
            # ----------------------------------------------------
            margin_score = 0
            if profit_margin is not None:
                if profit_margin > 0.15:
                    margin_score += 20
                elif profit_margin > 0:
                    margin_score += 10
                else:
                    margin_score += 0 # 적자면 가차없이 0점
            score_details["수익성(순이익)"] = (margin_score, 20, f"{profit_margin*100:.1f}%" if profit_margin else "데이터 없음")

            # ----------------------------------------------------
            # 3. 기술적 추세 - 25점 만점
            # ----------------------------------------------------
            tech_score = 0
            tech_notes = []
            
            if price > ma_200:
                tech_score += 15
                tech_notes.append("200일선 위 상승추세")
            
            if 40 <= rsi <= 60:
                tech_score += 10
                tech_notes.append("양호한 눌림목")
            elif rsi > 70:
                tech_score += 0
                tech_notes.append("단기 과열 (추격매수 금지)")

            score_details["차트 추세"] = (tech_score, 25, ", ".join(tech_notes) if tech_notes else "역배열 하락세")

            # ----------------------------------------------------
            # 4. 수급 (스마트머니 추적) - 15점 만점
            # ----------------------------------------------------
            vol_score = 0
            if current_volume > (avg_volume_10d * 1.2):
                vol_score += 15
                vol_desc = "평균 대비 120% 이상 거래량 폭발 (매집/관심 유입)"
            elif current_volume > avg_volume_10d:
                vol_score += 10
                vol_desc = "평균 거래량 상회 (양호)"
            else:
                vol_score += 5
                vol_desc = "평균 이하 거래량 (소외)"
                
            score_details["시장 수급"] = (vol_score, 15, vol_desc)

            # ----------------------------------------------------
            # 종합 계산
            # ----------------------------------------------------
            total_score = value_score + margin_score + tech_score + vol_score

            st.divider()
            st.subheader(f"{name} ({symbol.upper()})")
            st.write(f"**섹터:** {sector} | **현재가:** {price:,.2f}")

            col1, col2, col3 = st.columns(3)
            col1.metric("v3 종합 점수", f"{total_score} / 100")
            col2.metric("수익성(마진)", f"{profit_margin*100:.1f}%" if profit_margin else "N/A")
            
            vol_ratio = (current_volume / avg_volume_10d) * 100 if avg_volume_10d else 0
            col3.metric("최근 수급 강도", f"평균의 {vol_ratio:.0f}%")

            st.progress(total_score / 100)

            # 상세 내역
            st.write("📋 **섹터/미래실적 맞춤형 상세 채점**")
            for factor, (sc, max_sc, desc) in score_details.items():
                st.markdown(f"- **{factor}**: `{sc}/{max_sc}점` ({desc})")

            # 판정
            st.divider()
            if total_score >= 80:
                st.success("🟢 Chkbot v3 판정: A등급 후보 (내년 실적 턴어라운드 + 수급 유입)")
            elif total_score >= 60:
                st.warning("🟡 Chkbot v3 판정: B등급 관망 (나쁘지 않으나 확실한 모멘텀 대기)")
            else:
                st.error("🔴 Chkbot v3 판정: C등급 위험 (역성장 우려, 밸류에이션 부담 또는 소외주)")

            st.write("📈 **최근 1개년 주가 및 200일선**")
            chart_df = pd.DataFrame({
                "현재가": hist['Close'],
                "200일선": hist['Close'].rolling(200).mean()
            })
            st.line_chart(chart_df)
