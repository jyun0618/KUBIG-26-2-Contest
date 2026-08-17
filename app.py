import os

import streamlit as st
from dotenv import load_dotenv

from pipeline import run_pipeline

load_dotenv()

st.set_page_config(page_title="FinBridge Korea - Demo", page_icon="🏦", layout="centered")

EXAMPLES = [
    ("B1. 서류 안내", "거래목적 확인을 위해 재학증명서 또는 거주지 증빙 등 추가 서류가 요구될 수 있습니다."),
    ("B2. 송금 한도 안내", "1일 해외송금 한도는 미화 5만 달러이며, 최초 거래 시 여권과 외국인등록증 원본 제시가 필수입니다."),
    ("B3. 계좌개설 안내(영문)", "For your first bank visit, please bring your passport and Alien Registration Card. A certificate of enrollment may also be required depending on the bank."),
    ("C1. 기관사칭 문자", "[검찰청] 귀하의 계좌가 범죄에 연루되었습니다. 아래 링크에서 계좌정보를 입력하고 안전계좌로 자금을 이체하십시오."),
    ("C2. 정상 알림(비교용)", "[OO은행] 고객님의 체크카드가 08/11 14:20 승인되었습니다. 본인 사용이 아니면 콜센터로 문의하세요."),
    ("C3. 채용사기(영문)", "Congratulations! You are selected for a part-time job. Please send a 50,000 KRW registration fee to secure your position and provide your bank account and ID number."),
]

st.title("🏦 FinBridge Korea — Demo")
st.caption("외국인 금융 안내문 해석 + 의심 메시지 확인 Agent (프로토타입, 근거는 실제 공식문서 코퍼스 기반)")

if not os.environ.get("GEMINI_API_KEY"):
    st.warning("GEMINI_API_KEY가 설정되어 있지 않습니다. `.env` 파일에 키를 넣거나 터미널에서 export 하세요.", icon="⚠️")

st.subheader("예시 입력")
cols = st.columns(3)
if "user_text_area" not in st.session_state:
    st.session_state.user_text_area = ""

for i, (label, text) in enumerate(EXAMPLES):
    if cols[i % 3].button(label, use_container_width=True):
        st.session_state.user_text_area = text

user_text = st.text_area(
    "안내문, 문자메시지, 또는 금융 상황을 입력하세요",
    height=120,
    key="user_text_area",
)

run = st.button("분석하기", type="primary")

if run and user_text.strip():
    with st.spinner("분석 중..."):
        try:
            result = run_pipeline(user_text.strip())
        except Exception as e:
            st.error(f"오류 발생: {e}")
            result = None

    if result:
        extraction = result["extraction"]
        answer = result["answer"]
        chunks = result["chunks"]
        warnings = result["verification_warnings"]

        st.divider()
        st.markdown(f"**분류된 시나리오:** `{extraction.scenario}`  |  **언어:** `{extraction.language}`")

        st.subheader("1. 상황 요약")
        st.write(answer.situation_summary)

        st.subheader("2. 쉬운 설명")
        st.write(answer.plain_explanation)

        st.subheader("3. 핵심 정보")
        for item in answer.key_info:
            st.markdown(f"- {item}")

        if answer.risk_signals:
            st.subheader("4. ⚠️ 위험 신호")
            for item in answer.risk_signals:
                st.markdown(f"- 🔴 {item}")

        st.subheader("5. ✅ 지금 할 일")
        for item in answer.do_now:
            st.markdown(f"- {item}")

        if answer.do_not:
            st.subheader("6. 🚫 하지 말아야 할 일")
            for item in answer.do_not:
                st.markdown(f"- {item}")

        st.subheader("7. 📎 근거")
        for s in answer.sources:
            st.markdown(f"- {s}")

        if answer.unconfirmed:
            st.subheader("8. ❓ 확정할 수 없는 내용 (직접 확인 필요)")
            for item in answer.unconfirmed:
                st.markdown(f"- {item}")

        if warnings:
            st.subheader("🔍 자동 검증 경고 (데모용 간이 검증)")
            for w in warnings:
                st.markdown(f"- {w}")

        with st.expander("사용된 근거 원문 보기 (디버그)"):
            for c in chunks:
                st.markdown(f"**[{c['id']}] {c['institution']} - {c['document_title']} ({c['published_at']})**")
                st.caption(c["source_url"])
                st.write(c["text"])

        with st.expander("추출된 구조화 정보 (디버그)"):
            st.json(extraction.model_dump())
elif run:
    st.info("입력을 먼저 작성해주세요.")
