import streamlit as st
import pandas as pd
import re

# --- 앱 기본 설정 ---
st.set_page_config(page_title="보험 리모델링 전후 비교", layout="wide")

# --- 그룹별 항목 정의 ---
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
        with st.sidebar.expander(f"\U0001F4C2 {group}"):
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
st.title("\U0001F501 보험 리모델링 전후 비교 도구")

if "before_data" not in st.session_state:
    st.session_state.before_data = input_section("1️⃣ 기존 보장 내용", "before")
else:
    st.session_state.before_data = input_section("1️⃣ 기존 보장 내용", "before", st.session_state.before_data)

st.session_state.after_data = input_section("2️⃣ 제안 보장 내용", "after", st.session_state.before_data)

# --- 비교 실행 ---
if st.sidebar.button("\U0001F4CA 비교 시작"):
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
    st.subheader("\U0001F4CC 리모델링 요약")
    msg_lines = []

    if fee_diff > 0:
        msg_lines.append(f"\U0001F4B8 **월 보험료가 {fee_diff:,}원 절감**되어 경제적입니다.")
    elif fee_diff < 0:
        msg_lines.append(f"\U0001F4C8 **월 보험료가 {abs(fee_diff):,}원 증가**했지만 보장 강화가 목적일 수 있습니다.")
    else:
        msg_lines.append("⚖️ **월 보험료는 동일**합니다.")

    if total_diff > 0:
        msg_lines.append(f"\U0001F4C9 **총 납입 보험료도 {total_diff:,}원 줄어들어 효율적인 설계입니다.**")
    elif total_diff < 0:
        msg_lines.append(f"\U0001F4C8 **총 납입 보험료가 {abs(total_diff):,}원 늘어났습니다. 보장 항목과 비교해볼 필요가 있습니다.**")

    if year_diff > 0:
        msg_lines.append(f"⏱️ **납입기간이 {year_diff}년 단축**되어 부담이 줄었습니다.")
    elif year_diff < 0:
        msg_lines.append(f"\U0001F4C6 **납입기간이 {abs(year_diff)}년 연장**되어 장기적인 플랜이 적용되었습니다.")

    for m in msg_lines:
        st.info(m)

    # ✅ 보장 변화 요약 - 그룹별 2열 출력 (1열 먼저 출력 후 2열)
    st.subheader("✅ 보장 변화 요약")
    summary_dict = {}

    for group, items in bojang_groups.items():
        group_lines = []
        for item in items:
            b = before_data.get(item)
            a = after_data.get(item)
            if b != a:
                if isinstance(b, dict) and isinstance(a, dict):
                    b_amt = b.get("금액") or 0
                    a_amt = a.get("금액") or 0
                    diff = a_amt - b_amt
                    if diff > 0:
                        group_lines.append(f"\U0001F53C {item}: {b_amt:,}만원 → {a_amt:,}만원 (보장 강화)")
                    elif diff < 0:
                        group_lines.append(f"\U0001F53D {item}: {b_amt:,}만원 → {a_amt:,}만원 (보장 축소)")
                elif isinstance(b, str) and isinstance(a, str):
                    group_lines.append(f"\U0001F501 {item}: {b} → {a}")
        if group_lines:
            summary_dict[group] = group_lines

    if summary_dict:
        left_col, right_col = st.columns(2)
        groups = list(summary_dict.items())
        half = (len(groups) + 1) // 2
        for i in range(len(groups)):
            group, lines = groups[i]
            with (left_col if i < half else right_col):
                st.markdown(f"#### \U0001F4C2 {group}")
                for line in lines:
                    st.markdown(f"- {line}")

    st.caption(f"총 변화 항목 수: {sum(len(v) for v in summary_dict.values())}개")
