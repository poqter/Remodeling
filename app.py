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
def input_section(title, key_prefix):
    st.sidebar.subheader(title)
    result = {}
    for group, items in bojang_groups.items():
        with st.sidebar.expander(f"📂 {group}"):
            for item in items:
                full_key = f"{key_prefix}_{item}"
                if "실손" in item:
                    val = st.radio(f"{item}", ["", "예", "아니오"], key=full_key, horizontal=True)
                    result[item] = val
                else:
                    amt = st.text_input(f"{item} (만원)", key=full_key)
                    nap_key = f"{full_key}_nap"
                    ren_key = f"{full_key}_ren"
                    nap = st.selectbox(f"납입기간 ({item})", ["", "10년납", "20년납", "30년납", "전기납"], key=nap_key)
                    ren = st.selectbox(f"갱신여부 ({item})", ["", "갱신형", "비갱신형"], key=ren_key)
                    result[item] = {"금액": parse_amount(amt), "납입": nap, "갱신": ren}
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

    before_data = input_section("1️⃣ 기존 보장 내용", "before")
    after_data = input_section("2️⃣ 제안 보장 내용", "after")

    if st.sidebar.button("🔍 비교 시작"):
        st.session_state.before_data = before_data
        st.session_state.after_data = after_data
        st.success("비교 데이터가 저장되었습니다.")

if "before_data" in st.session_state and "after_data" in st.session_state:
    before_data = st.session_state.before_data
    after_data = st.session_state.after_data

    강화수, 축소수, 총기존, 총제안 = 0, 0, 0, 0
    for k in before_data:
        b, a = before_data[k], after_data.get(k)
        if isinstance(b, dict) and isinstance(a, dict):
            b_amt, a_amt = b.get("금액") or 0, a.get("금액") or 0
            총기존 += b_amt
            총제안 += a_amt
            if a_amt > b_amt: 강화수 += 1
            elif a_amt < b_amt: 축소수 += 1

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

    diff_list, all_list = [], []
    for group, items in bojang_groups.items():
        for item in items:
            b, a = before_data.get(item), after_data.get(item)
            if isinstance(b, str) and isinstance(a, str):
                row = {"항목": item, "기존": b or "없음", "제안": a or "없음", "구분": group}
                if b != a: diff_list.append(row)
                all_list.append(row)
            elif isinstance(b, dict) and isinstance(a, dict):
                row = {
                    "항목": item,
                    "기존금액": b.get("금액"),
                    "제안금액": a.get("금액"),
                    "납입기간": f"{b.get('납입')} → {a.get('납입')}" if b.get("납입") != a.get("납입") else b.get("납입"),
                    "갱신여부": f"{b.get('갱신')} → {a.get('갱신')}" if b.get("갱신") != a.get("갱신") else b.get("갱신"),
                    "구분": group
                }
                if b != a: diff_list.append(row)
                all_list.append(row)

    if print_mode and 요약표_표시:
        st.subheader("🔍 변화 항목 요약표")
        st.dataframe(pd.DataFrame(diff_list))

    if not print_mode:
        st.subheader("🔍 변화 있는 항목")
        for row in diff_list:
            기존 = row.get("기존금액") or 0
            제안 = row.get("제안금액") or 0
            배경색 = "#e0f7e9" if 제안 > 기존 else "#ffe0e0"
            st.markdown(f"""
            <div style='border-radius:12px; padding:15px; margin-bottom:10px; background-color:{배경색}; border: 1px solid #ccc;'>
                <strong>{row['항목']}</strong><br>
                ✅ 기존: {기존}만원<br>
                🔁 제안: {제안}만원<br>
                📅 납입기간: {row.get('납입기간', '-')}, 🔄 갱신여부: {row.get('갱신여부', '-')}
            </div>""", unsafe_allow_html=True)

        st.subheader("📋 전체 항목 보기")
        st.dataframe(pd.DataFrame(all_list))