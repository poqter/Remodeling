import streamlit as st
import pandas as pd
import re

# --- 앱 기본 설정 ---
st.set_page_config(page_title="보험 리모델링 전후 비교", layout="wide")

# --- 그룹별 항목 정의 ---
bojang_groups = {
    "사망": ["일반사망", "질병사망", "재해(상해)사망"],
    "장해": ["질병후유장해", "재해(상해)장해"],
    "암": ["통합암", "일반암", "유사암", "암치료"],
    "뇌/심장": ["뇌혈관", "뇌졸중", "뇌출혈", "초기심장질환", "허혈성심장질환", "급성심근경색증"],
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

# --- 입력 폼 구성 ---
def input_section(title, key_prefix, default_data=None):
    st.sidebar.subheader(title)
    result = {}

    def get_default_value(field):
        if default_data and field in default_data:
            return default_data.get(field, "")
        return ""

    result["총월보험료"] = st.sidebar.text_input(f"{title} - 총 월 보험료(원)", value=get_default_value("총월보험료"), key=f"{key_prefix}_월보험료")
    result["납입기간"] = st.sidebar.text_input(f"{title} - 납입기간(년)", value=get_default_value("납입기간"), key=f"{key_prefix}_납입기간")
    result["총납입보험료"] = st.sidebar.text_input(f"{title} - 총 납입 보험료 (원, 선택)", value=get_default_value("총납입보험료"), key=f"{key_prefix}_총납입")

    for group, items in bojang_groups.items():
        with st.sidebar.expander(f"📂 {group}"):
            for item in items:
                full_key = f"{key_prefix}_{item}"
                default_value = ""
                if default_data:
                    if isinstance(default_data.get(item), dict):
                        default_value = default_data[item].get("금액", "")
                    else:
                        default_value = default_data.get(item, "")

                if "실손" in item:
                    val = st.radio(f"{item}", ["", "예", "아니오"], key=full_key, horizontal=True, index=["", "예", "아니오"].index(default_value) if default_value in ["", "예", "아니오"] else 0)
                    result[item] = val
                else:
                    amt = st.text_input(f"{item} (만원)", value=str(default_value) if default_value else "", key=full_key)
                    result[item] = {"금액": parse_amount(amt)}
    return result

# --- 기존/제안 보장 입력 ---
st.title("🔄 보험 리모델링 전후 비교 도구")

if "before_data" not in st.session_state:
    st.session_state.before_data = input_section("1️⃣ 기존 보장 내용", "before")
else:
    st.session_state.before_data = input_section("1️⃣ 기존 보장 내용", "before", st.session_state.before_data)

st.session_state.after_data = input_section("2️⃣ 제안 보장 내용", "after", st.session_state.before_data)

# --- 사이드바 버튼 ---
compare_trigger = st.sidebar.button("📊 비교 시작")

# --- 비교 실행 ---
if compare_trigger:
    before_data = st.session_state.before_data
    after_data = st.session_state.after_data

    before_fee = parse_amount(before_data.get("총월보험료")) or 0
    after_fee = parse_amount(after_data.get("총월보험료")) or 0
    before_total = parse_amount(before_data.get("총납입보험료")) or 0
    after_total = parse_amount(after_data.get("총납입보험료")) or 0
    before_years = parse_amount(before_data.get("납입기간")) or 0
    after_years = parse_amount(after_data.get("납입기간")) or 0

    fee_diff = before_fee - after_fee
    total_diff = before_total - after_total
    year_diff = before_years - after_years

    # 상단 평가 메시지
    st.subheader("📌 리모델링 요약")
    msg = ""
    if fee_diff > 0:
        msg += f"💸 월 보험료가 **{fee_diff:,}원 절감**되었습니다."
    elif fee_diff < 0:
        msg += f"📈 월 보험료가 **{abs(fee_diff):,}원 증가**했습니다."
    else:
        msg += "⚖️ 월 보험료는 변화가 없습니다."

    if total_diff > 0:
        msg += f" 총 납입 보험료는 **{total_diff:,}원 절감**됩니다."
    elif total_diff < 0:
        msg += f" 총 납입 보험료는 **{abs(total_diff):,}원 증가**합니다."

    if year_diff > 0:
        msg += f" 납입기간이 **{year_diff}년 단축**되었습니다."
    elif year_diff < 0:
        msg += f" 납입기간이 **{abs(year_diff)}년 연장**되었습니다."

    st.success(msg)

    # 항목 변화 요약
    st.subheader("✅ 보장 변화 요약")
    change_count = 0
    for group, items in bojang_groups.items():
        for item in items:
            b = before_data.get(item)
            a = after_data.get(item)

            if isinstance(b, dict) and isinstance(a, dict):
                b_amt, a_amt = b.get("금액") or 0, a.get("금액") or 0
                if b_amt != a_amt:
                    change_count += 1
                    st.markdown(f"- **{item}**: {b_amt:,}만원 → {a_amt:,}만원")
            elif isinstance(b, str) and isinstance(a, str):
                if b != a:
                    change_count += 1
                    st.markdown(f"- **{item}**: {b} → {a}")

    st.caption(f"총 변화 항목 수: {change_count}개")