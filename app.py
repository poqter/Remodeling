import streamlit as st
import pandas as pd
import re

# --- 앱 기본 설정 ---
st.set_page_config(page_title="보험 리모델링 전후 비교", layout="wide")

# --- 인쇄모드 설정 ---
print_mode = st.sidebar.toggle("🖨️ 인쇄모드로 보기", value=False)
요약표_표시 = st.sidebar.checkbox("변화 항목만 요약표 보기 (인쇄용)", value=True) if print_mode else False

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

# --- 본문 실행 흐름 ---
if print_mode:
    st.markdown("""
        <style>
        .block-container { padding: 20px; background-color: white; color: black; }
        </style>
    """, unsafe_allow_html=True)
    st.title("🖨️ 보험 리모델링 비교 리포트 (인쇄용)")
else:
    st.title("📋 보험 리모델링 전후 비교 시뮬레이터")

st.sidebar.title("📝 보장 내용 입력")
st.sidebar.markdown("금액 단위는 '만원', 실손은 가입 여부만 체크")

if not print_mode:
    if st.sidebar.button("🔄 전체 리셋"):
        st.session_state.clear()
        st.experimental_rerun()

    if "before_data" not in st.session_state:
        st.session_state.before_data = input_section("1️⃣ 기존 보장 내용", "before")
    else:
        input_section("1️⃣ 기존 보장 내용", "before", st.session_state.before_data)

    after_data = input_section("2️⃣ 제안 보장 내용", "after", st.session_state.before_data)

    if st.sidebar.button("🔍 비교 시작"):
        st.session_state.after_data = after_data
        st.success("비교 데이터가 저장되었습니다.")

if "before_data" in st.session_state and "after_data" in st.session_state:
    before_data = st.session_state.before_data
    after_data = st.session_state.after_data

    강화수, 축소수, 총기존, 총제안 = 0, 0, 0, 0
    요약문 = []

    for group, items in bojang_groups.items():
        for item in items:
            b, a = before_data.get(item), after_data.get(item)
            if isinstance(b, dict) and isinstance(a, dict):
                b_amt, a_amt = b.get("금액") or 0, a.get("금액") or 0
                총기존 += b_amt
                총제안 += a_amt
                if b_amt != a_amt:
                    if b_amt == 0:
                        요약문.append(f"📌 {item}: 신설 {a_amt}만원 ✅")
                    elif a_amt == 0:
                        요약문.append(f"📌 {item}: 삭제됨 ❌")
                    elif a_amt > b_amt:
                        요약문.append(f"📌 {item}: {b_amt} → {a_amt}만원 (강화 ✅)")
                        강화수 += 1
                    else:
                        요약문.append(f"📌 {item}: {b_amt} → {a_amt}만원 (축소 ⚠️)")
                        축소수 += 1
            elif isinstance(b, str) and isinstance(a, str):
                if b != a:
                    요약문.append(f"📌 {item}: {b or '없음'} → {a or '없음'}")

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

    st.subheader("🔍 변화 요약")
    for line in 요약문:
        st.markdown(line)

    if print_mode and 요약표_표시:
        st.subheader("📋 변화 항목 표")
        st.dataframe(pd.DataFrame(요약문, columns=["요약 내용"]))
