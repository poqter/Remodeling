import streamlit as st
import pandas as pd
import re

# --- 앱 기본 설정 ---
st.set_page_config(page_title="보험 리모델링 전후 비교", layout="wide")

# --- 인쇄모드 진입 여부 ---
print_mode = st.sidebar.toggle("🖨️ 인쇄모드로 보기", value=False)
요약표_표시 = st.sidebar.checkbox("변화 항목만 요약표 보기 (인쇄용)", value=True) if print_mode else False

if print_mode:
    st.markdown("""
        <style>
        .block-container {
            padding: 20px;
            background-color: white;
            color: black;
        }
        </style>
    """, unsafe_allow_html=True)
    st.title("🖨️ 보험 리모델링 비교 리포트 (인쇄용)")

    # 종합 평가 메시지 (인쇄 상단용 예시)
    if "before_data" in st.session_state and "after_data" in st.session_state:
        강화수 = 0
        축소수 = 0
        총기존 = 0
        총제안 = 0

        for item in st.session_state.before_data:
            b = st.session_state.before_data.get(item)
            a = st.session_state.after_data.get(item)
            if isinstance(b, dict) and isinstance(a, dict):
                b_amt = b.get("금액") or 0
                a_amt = a.get("금액") or 0
                총기존 += b_amt
                총제안 += a_amt
                if a_amt > b_amt:
                    강화수 += 1
                elif a_amt < b_amt:
                    축소수 += 1

        차이 = 총제안 - 총기존
        평가 = ""
        if 차이 < 0:
            평가 += f"💰 보험료가 {abs(차이)}만원 절감되었어요!  "
        elif 차이 > 0:
            평가 += f"📈 보장이 강화되며 보험료가 {차이}만원 증가했어요.  "
        else:
            평가 += "⚖️ 보험료는 동일합니다.  "

        평가 += f"🛡️ 강화된 항목: {강화수}개, 🔻 축소된 항목: {축소수}개"
        st.success(평가)

        # 변화 항목 요약표 (선택)
        if 요약표_표시:
            st.markdown("## 🔍 변화 항목 요약표")
            diff_rows = []
            for group, items in st.session_state.before_data.items():
                for item in items:
                    b = st.session_state.before_data.get(item)
                    a = st.session_state.after_data.get(item)
                    if isinstance(b, dict) and isinstance(a, dict) and b != a:
                        diff_rows.append({
                            "항목": item,
                            "기존금액": b.get("금액"),
                            "제안금액": a.get("금액")
                        })
                    elif isinstance(b, str) and isinstance(a, str) and b != a:
                        diff_rows.append({"항목": item, "기존": b, "제안": a})
            if diff_rows:
                st.dataframe(pd.DataFrame(diff_rows))
            else:
                st.info("변화된 항목이 없습니다.")
else:
    st.title("📋 보험 리모델링 전후 비교 시뮬레이터")
