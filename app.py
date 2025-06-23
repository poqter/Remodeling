import streamlit as st
import pandas as pd
import re

# --- 앱 기본 설정 ---
st.set_page_config(page_title="보험 리모델링 전후 비교", layout="wide")

# --- 그룹별 항목 정의 (우선순위: 사망, 암, 뇌/심장 순) ---
bojang_groups = {
    "사망": ["일반사망", "질병사망", "재해(상해)사망"],
    "암": ["통합암", "일반암", "유사암", "암치료"],
    "뇌/심장": ["뇌혈관", "뇌졸중", "뇌출혈", "초기심장질환", "허혈성심장질환", "급성심근경색증"],
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

# --- 카드 시각화 함수 ---
def display_change_card(item, before, after):
    if isinstance(before, dict) and isinstance(after, dict):
        b_amt = before.get("금액") or 0
        a_amt = after.get("금액") or 0
        if b_amt != a_amt:
            color = "#d4f4dd" if a_amt > b_amt else "#ffe1e1"
            diff = a_amt - b_amt
            label = "보장 강화" if diff > 0 else "보장 축소"
            return f"""
                <div style='background-color:{color}; padding:15px; border-radius:10px; margin:10px;'>
                    <strong>{item}</strong><br>
                    {b_amt:,}만원 → <strong>{a_amt:,}만원</strong><br>
                    <span style='color:gray;'>({label})</span>
                </div>
            """
    elif isinstance(before, str) and isinstance(after, str):
        if before != after:
            if before == "" and after in ["예", "아니오"]:
                label = "신규 추가"
                color = "#e0f7fa"
            elif after == "" and before in ["예", "아니오"]:
                label = "삭제"
                color = "#fce4ec"
            else:
                label = "변경"
                color = "#fff9c4"
            return f"""
                <div style='background-color:{color}; padding:15px; border-radius:10px; margin:10px;'>
                    <strong>{item}</strong><br>
                    {before} → <strong>{after}</strong><br>
                    <span style='color:gray;'>({label})</span>
                </div>
            """
    return None

# --- 비교 실행 ---
if st.sidebar.button("📊 비교 시작"):
    before = st.session_state.before_data
    after = st.session_state.after_data

    before_fee = parse_amount(before.get("총월보험료")) or 0
    after_fee = parse_amount(after.get("총월보험료")) or 0
    before_total = parse_amount(before.get("총납입보험료")) or 0
    after_total = parse_amount(after.get("총납입보험료")) or 0
    before_years = parse_amount(before.get("납입기간")) or 0
    after_years = parse_amount(after.get("납입기간")) or 0

    fee_diff = before_fee - after_fee
    total_diff = before_total - after_total
    year_diff = before_years - after_years

    st.subheader("📌 리모델링 요약")
    if fee_diff > 0:
        st.info(f"💸 **월 보험료가 {fee_diff:,}원 절감**되어 경제적입니다.")
    elif fee_diff < 0:
        st.info(f"📈 **월 보험료가 {abs(fee_diff):,}원 증가**했지만 보장 강화가 목적일 수 있습니다.")
    else:
        st.info("⚖️ **월 보험료는 동일**합니다.")

    if year_diff > 0:
        st.info(f"⏱️ **납입기간이 {year_diff}년 단축**되어 부담이 줄었습니다.")
    elif year_diff < 0:
        st.info(f"📆 **납입기간이 {abs(year_diff)}년 연장**되어 장기적인 플랜이 적용되었습니다.")

    if total_diff > 0:
        year_saving = round(total_diff / (after_fee or 1) / 12, 1)
        st.info(f"📉 **총 납입 보험료도 {total_diff:,}원 절감** → 약 **{year_saving}년치 보험료** 차이입니다.")
    elif total_diff < 0:
        st.info(f"📈 **총 납입 보험료가 {abs(total_diff):,}원 증가** → 보장 항목에 따른 확인 필요.")

    st.subheader("✅ 보장 변화 요약")
    col1, col2 = st.columns(2)
    stats = {"보장 강화": 0, "보장 축소": 0, "신규 추가": 0, "삭제": 0}
    i = 0

    for group in bojang_groups:
        for item in bojang_groups[group]:
            b = before.get(item)
            a = after.get(item)
            if b != a:
                card = display_change_card(item, b, a)
                if card:
                    if isinstance(b, dict) and isinstance(a, dict):
                        if (a.get("금액") or 0) > (b.get("금액") or 0):
                            stats["보장 강화"] += 1
                        else:
                            stats["보장 축소"] += 1
                    elif isinstance(b, str) and isinstance(a, str):
                        if b == "" and a in ["예", "아니오"]:
                            stats["신규 추가"] += 1
                        elif a == "" and b in ["예", "아니오"]:
                            stats["삭제"] += 1
                    (col1 if i % 2 == 0 else col2).markdown(card, unsafe_allow_html=True)
                    i += 1

    st.caption(f"🔎 총 변화 항목 수: {sum(stats.values())}개 | 🟢 보장 강화: {stats['보장 강화']}  🔴 보장 축소: {stats['보장 축소']}  🆕 신규 추가: {stats['신규 추가']}  ❌ 삭제: {stats['삭제']}")