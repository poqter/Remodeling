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

# --- 항목 입력 렌더링 함수 ---
def render_item_input(item, key, default_value):
    if "실손" in item:
        val = st.radio(f"{item}", ["", "예", "아니오"],
                       key=key, horizontal=True,
                       index=["", "예", "아니오"].index(default_value) if default_value in ["", "예", "아니오"] else 0)
        return val
    else:
        amt = st.text_input(f"{item} (만원)", value=str(default_value) if default_value else "", key=key)
        return {"금액": parse_amount(amt)}

# --- 보장 입력 섹션 ---
def input_section(title, key_prefix, default_data=None):
    st.sidebar.subheader(title)
    result = {
        "총월보험료": st.sidebar.text_input(f"{title} - 총 월 보험료(원)", value=default_data.get("총월보험료", ""), key=f"{key_prefix}_월보험료"),
        "납입기간": st.sidebar.text_input(f"{title} - 납입기간(년)", value=default_data.get("납입기간", ""), key=f"{key_prefix}_납입기간"),
        "총납입보험료": st.sidebar.text_input(f"{title} - 총 납입 보험료(원)", value=default_data.get("총납입보험료", ""), key=f"{key_prefix}_총납입")
    }

    for group, items in bojang_groups.items():
        with st.sidebar.expander(f"📂 {group}"):
            for item in items:
                key = f"{key_prefix}_{item}"
                raw = default_data.get(item, "")
                default_val = raw.get("금액") if isinstance(raw, dict) else raw
                result[item] = render_item_input(item, key, default_val)
    return result

# --- 카드 출력 함수 ---
def display_change_card(item, before, after):
    if isinstance(before, dict) and isinstance(after, dict):
        b_amt = before.get("금액", 0)
        a_amt = after.get("금액", 0)
        if b_amt != a_amt:
            color = "#d4f4dd" if a_amt > b_amt else "#ffe1e1"
            change = "보장 강화" if a_amt > b_amt else "보장 축소"
            return f"""
                <div style='background-color:{color}; padding:15px; border-radius:10px; margin:10px;'>
                    <strong>{item}</strong><br>{b_amt:,}만원 → <strong>{a_amt:,}만원</strong><br>
                    <span style='color:gray;'>({change})</span>
                </div>
            """
    elif isinstance(before, str) and isinstance(after, str) and before != after:
        color = "#d4f4dd" if after == "예" else "#ffe1e1"
        return f"""
            <div style='background-color:{color}; padding:15px; border-radius:10px; margin:10px;'>
                <strong>{item}</strong><br>{before} → <strong>{after}</strong>
            </div>
        """
    return None

# --- 페이지 본문 ---
st.title("🔄 보험 리모델링 전후 비교 도구")

if "before_data" not in st.session_state:
    st.session_state.before_data = {}

before_data_input = input_section("1️⃣ 기존 보장 내용", "before", st.session_state.before_data)
st.session_state.before_data = before_data_input

after_data_input = input_section("2️⃣ 제안 보장 내용", "after", st.session_state.before_data)
st.session_state.after_data = after_data_input

compare_trigger = st.sidebar.button("📊 비교 시작")

# --- 비교 결과 출력 ---
if compare_trigger:
    before_data = st.session_state.before_data
    after_data = st.session_state.after_data

    before_fee = parse_amount(before_data.get("총월보험료")) or 0
    after_fee = parse_amount(after_data.get("총월보험료")) or 0
    before_total = parse_amount(before_data.get("총납입보험료")) or 0
    after_total = parse_amount(after_data.get("총납입보험료")) or 0
    before_years = parse_amount(before_data.get("납입기간")) or 0
    after_years = parse_amount(after_data.get("납입기간")) or 0

    fee_diff = after_fee - before_fee
    total_diff = after_total - before_total
    year_diff = after_years - before_years

    st.subheader("📌 리모델링 요약")
    if fee_diff > 0:
        st.info(f"📈 **월 보험료가 {fee_diff:,}원 증가**했지만 보장 강화가 목적일 수 있습니다.")
    elif fee_diff < 0:
        st.info(f"💸 **월 보험료가 {abs(fee_diff):,}원 절감**되어 경제적입니다.")
    else:
        st.info("⚖️ **월 보험료는 동일**합니다.")

    if total_diff > 0:
        st.info(f"📈 **총 납입 보험료가 {total_diff:,}원 늘어났습니다. 보장 항목과 비교해볼 필요가 있습니다.**")
    elif total_diff < 0:
        st.info(f"📉 **총 납입 보험료도 {abs(total_diff):,}원 줄어들어 효율적인 설계입니다.**")

    if year_diff > 0:
        st.info(f"📆 **납입기간이 {year_diff}년 연장**되어 장기적인 플랜이 적용되었습니다.")
    elif year_diff < 0:
        st.info(f"⏱️ **납입기간이 {abs(year_diff)}년 단축**되어 부담이 줄었습니다.")

    # 보장 항목 변화 시각화
    st.subheader("✅ 보장 변화 요약")
    col1, col2 = st.columns(2)
    change_count = 0

    for group in bojang_groups:
        for item in bojang_groups[group]:
            b = before_data.get(item)
            a = after_data.get(item)
            if b != a:
                card_html = display_change_card(item, b, a)
                if card_html:
                    (col1 if change_count % 2 == 0 else col2).markdown(card_html, unsafe_allow_html=True)
                    change_count += 1

    st.caption(f"총 변화 항목 수: {change_count}개")