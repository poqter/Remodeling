import streamlit as st
import pandas as pd
import re

# --- 앱 기본 설정 ---
st.set_page_config(page_title="보험 리모델링 전후 비교", layout="wide")

# --- 그룹별 항목 정의 ---
bojang_groups = {
    "암": ["통합암", "일반암", "유사암", "암치료"],
    "뇌/심장": ["뇌혈관", "뇌졸중", "뇌출혈", "초기심장질환", "허혈성심장질환", "급성심근경색증"],
    "사망": ["일반사망", "질병사망", "재해(상해)사망"],
    "장해": ["질병후유장해", "재해(상해)장해"],
    "수술": ["질병수술", "질병종수술", "상해수술", "상해종수술"],
    "입원": ["질병입원", "상해입원", "간병인"],
    "기타": [
        "교통사고처리지원금", "스쿨존사고처리지원금", "변호사선임비용",
        "운전자벌금(대인)", "운전자벌금(대물)", "자동차사고부상위로금",
        "일상생활배상책임", "치아보철치료비", "치아보존치료비", "골절진단비"
    ],
    "실손": ["질병입원(실손)", "질병통원(실손)", "상해입원(실손)", "상해통원(실손)"]
}

# --- 숫자 추출 함수 ---
def parse_amount(text):
    if not text:
        return None
    try:
        return int(re.sub(r"[^\d]", "", text))
    except:
        return None

# --- 카드 시각화 함수 (좌우 비교 스타일) ---
def display_change_card(item, before, after):
    if isinstance(before, dict) and isinstance(after, dict):
        b_amt = before.get("금액") or 0
        a_amt = after.get("금액") or 0
        if b_amt != a_amt:
            color = "#d4f4dd" if a_amt > b_amt else "#ffe1e1"
            diff = a_amt - b_amt
            col1, col2 = st.columns(2)
            with col1:
                st.markdown(f"""
                    <div style='background-color:#f9f9f9; padding:12px; border-radius:10px;'>
                        <strong>📌 {item} (기존)</strong><br>
                        {b_amt:,}만원
                    </div>
                """, unsafe_allow_html=True)
            with col2:
                st.markdown(f"""
                    <div style='background-color:{color}; padding:12px; border-radius:10px;'>
                        <strong>✅ {item} (제안)</strong><br>
                        {a_amt:,}만원 <span style='color:gray;'>({"보장 강화" if diff > 0 else "보장 축소"})</span>
                    </div>
                """, unsafe_allow_html=True)
    elif isinstance(before, str) and isinstance(after, str):
        if before != after:
            color = "#d4f4dd" if after == "예" else "#ffe1e1"
            col1, col2 = st.columns(2)
            with col1:
                st.markdown(f"""
                    <div style='background-color:#f9f9f9; padding:12px; border-radius:10px;'>
                        <strong>📌 {item} (기존)</strong><br>
                        {before}
                    </div>
                """, unsafe_allow_html=True)
            with col2:
                st.markdown(f"""
                    <div style='background-color:{color}; padding:12px; border-radius:10px;'>
                        <strong>✅ {item} (제안)</strong><br>
                        {after}
                    </div>
                """, unsafe_allow_html=True)
