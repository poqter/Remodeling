import streamlit as st
import pandas as pd
import re

# --- 앱 기본 설정 ---
st.set_page_config(page_title="보험 리모델링 전/후 비교", layout="wide")

# --- 그룹별 항목 정의 ---
bojang_groups = {
    "사망": ["일반사망", "질병사망", "재해(상해)사망"],
    "장해": ["질병후유장해", "재해(상해)장해"],    
    "암": ["통합암", "일반암", "유사암", "암치료"],
    "뇌/심장": ["뇌혈관", "뇌졸중", "뇌출혈", "초기심장질환", "허혈성심장질환", "급성심근경색증", "뇌/심치료"],
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
        with st.sidebar.expander(f"📂 {group}", expanded=True):
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
st.title("🔁 보험 리모델링 전/후 비교")

if "before_data" not in st.session_state:
    st.session_state.before_data = input_section("1️⃣ 기존 보장 내용", "before")
else:
    st.session_state.before_data = input_section("1️⃣ 기존 보장 내용", "before", st.session_state.before_data)

st.session_state.after_data = input_section("2️⃣ 제안 보장 내용", "after", st.session_state.before_data)

# --- 비교 실행 ---
if st.sidebar.button("📊 비교 시작"):
    st.session_state["compare_ready"] = True

if st.session_state.get("compare_ready"):
    pages = ["요약", "비교결과", "보장 변화 요약", "기대 효과 요약"]
    selected_page = st.select_slider("➡️ 페이지를 넘겨보세요", options=pages)

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

    summary_dict = {}
    강화, 축소, 신규, 삭제 = 0, 0, 0, 0
    기대효과_후보 = []
    비교결과_카드 = []

    for group, items in bojang_groups.items():
        group_lines = []
        for item in items:
            b = before_data.get(item)
            a = after_data.get(item)
            if b != a:
                if (not b or (isinstance(b, dict) and (b.get("금액") or 0) == 0)) and isinstance(a, dict) and (a.get("금액") or 0) > 0:
                    a_amt = a.get("금액") or 0
                    msg = f"🟢 {item}: 0만원 → {a_amt:,}만원 (신규 추가)"
                    group_lines.append(msg)
                    비교결과_카드.append((item, msg))
                    신규 += 1
                elif b and not a:
                    b_amt = b.get("금액") if isinstance(b, dict) else None
                    if b_amt is not None:
                        msg = f"🔴 {item}: {b_amt:,}만원 → 0만원 (삭제)"
                    else:
                        msg = f"🔴 {item}: 삭제"
                    group_lines.append(msg)
                    비교결과_카드.append((item, msg))
                    삭제 += 1
                elif isinstance(b, dict) and isinstance(a, dict):
                    b_amt = b.get("금액") or 0
                    a_amt = a.get("금액") or 0
                    diff = a_amt - b_amt
                    if diff > 0:
                        msg = f"🟦 {item}: {b_amt:,}만원 → {a_amt:,}만원 (보장 강화)"
                        강화 += 1
                    elif diff < 0:
                        msg = f"🟨 {item}: {b_amt:,}만원 → {a_amt:,}만원 (보장 축소)"
                        축소 += 1
                    else:
                        msg = None
                    if msg:
                        group_lines.append(msg)
                        비교결과_카드.append((item, msg))
                elif isinstance(b, str) and isinstance(a, str):
                    msg = f"🟣 {item}: {b} → {a} (형태 변경)"
                    group_lines.append(msg)
                    비교결과_카드.append((item, msg))
        if group_lines:
            summary_dict[group] = group_lines

    if selected_page == "요약":
        st.subheader("📌 리모델링 요약")
        if fee_diff > 0:
            st.markdown(f"- 💸 **월 보험료가 {fee_diff:,}원 절감**되어 경제적입니다.")
        elif fee_diff < 0:
            st.markdown(f"- 📈 **월 보험료가 {abs(fee_diff):,}원 증가**했지만 보장 강화 목적일 수 있습니다.")
        else:
            st.markdown("- ⚖️ **월 보험료는 동일**합니다.")

        if total_diff > 0:
            if after_fee > 0:
                months = total_diff // after_fee
                years = months // 12
                remainder_months = months % 12
                duration = f"약 {years}년 {remainder_months}개월" if years > 0 else f"약 {remainder_months}개월"
                st.markdown(f"- 📉 **총 납입 보험료가 {total_diff:,}원 줄어들어 효율적인 설계입니다.** 💡 *현재 보험료 기준으로 {duration} 동안 납입 가능해요.*")
            else:
                st.markdown(f"- 📉 **총 납입 보험료가 {total_diff:,}원 줄어들어 효율적인 설계입니다.**")
        elif total_diff < 0:
            st.markdown(f"- 📈 **총 납입 보험료가 {abs(total_diff):,}원 늘어났습니다. 보장 항목과 비교해볼 필요가 있습니다.**")

        if year_diff > 0:
            st.markdown(f"- ⏱️ **납입기간이 {year_diff}년 단축**되어 부담이 줄었습니다.")
        elif year_diff < 0:
            st.markdown(f"- 📆 **납입기간이 {abs(year_diff)}년 연장**되어 장기적인 플랜이 적용되었습니다.")

    elif selected_page == "비교결과":
        st.subheader("📊 보장 비교 결과")
        for item, msg in 비교결과_카드:
            st.markdown(f"- {msg}")

    elif selected_page == "보장 변화 요약":
        st.subheader("📌 보장 변화 요약")
        left_col, right_col = st.columns(2)
        all_groups = list(summary_dict.items())
        total_lines = sum(len(lines) for lines in summary_dict.values())
        cutoff = (total_lines + 1) // 2
        line_count = 0
        left_items, right_items = [], []
        for group, lines in all_groups:
            if line_count < cutoff:
                left_items.append((group, lines))
                line_count += len(lines)
            else:
                right_items.append((group, lines))

        with left_col:
            for group, lines in left_items:
                st.markdown(f"#### 📂 {group}")
                for line in lines:
                    st.markdown(f"- {line}")
        with right_col:
            for group, lines in right_items:
                st.markdown(f"#### 📂 {group}")
                for line in lines:
                    st.markdown(f"- {line}")

    elif selected_page == "기대 효과 요약":
        st.subheader("🌟 기대 효과 요약")
        if after_fee < before_fee:
            기대효과_후보.append("💸 월 보험료가 절감되어 가계 지출의 여유가 생깁니다.")
        elif after_fee > before_fee and (강화 + 신규) > 0:
            기대효과_후보.append("📈 월 보험료는 증가했지만, 보장 강화와 신규 보장 추가로 실질적인 대비가 향상되었습니다.")

        if after_total < before_total:
            기대효과_후보.append("🎯 총 보험료가 절감되어 절약된 금액을 다른 재무 계획에 활용할 수 있습니다.")
        elif after_total > before_total:
            기대효과_후보.append("💰 총 납입 보험료는 증가했지만, 장기적인 재정 리스크에 대한 방어가 확보되었습니다.")

        if after_years < before_years:
            기대효과_후보.append("🚀 납입기간이 단축되어 조기 자산 완결과 부담 경감 효과가 있습니다.")

        if 신규 > 0:
            기대효과_후보.append(f"🌱 신규 보장 {신규}개가 추가되어 기존에 없던 리스크에 대응이 가능해졌습니다.")
        if 강화 > 0:
            기대효과_후보.append(f"🛡️ 보장 강화 {강화}개로 실질적인 사고·질병 발생 시 도움의 폭이 넓어졌습니다.")
        if 삭제 > 0:
            기대효과_후보.append("🧹 중복되거나 효율이 낮은 보장이 제거되어 보험 구조가 간결해졌습니다.")
        if 축소 == 0 and 삭제 == 0 and (강화 + 신규 > 0):
            기대효과_후보.append("✅ 보장 축소 없이 보장 범위만 확장되어 매우 안정적인 리모델링이 되었습니다.")

        if 기대효과_후보:
            for 문장 in 기대효과_후보:
                st.markdown(f"- {문장}")
        else:
            st.markdown("📎 리모델링으로 인한 주요 변화는 감지되지 않았습니다. 입력 값을 다시 확인해주세요.")

# --- 제작자 정보 ---
st.sidebar.markdown("---")
st.sidebar.markdown("👨‍💻 **제작자**: 비전본부 드림지점 박병선 팀장")
st.sidebar.markdown("🗓️ **버전**: v1.0.1")
st.sidebar.markdown("📅 **최종 업데이트**: 2025-07-05")
