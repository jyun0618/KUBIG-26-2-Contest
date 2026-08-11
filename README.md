# FinBridge Korea — 90분 데모

시나리오 B(안내문 해석) + C(의심 메시지 확인)만 다루는 초경량 프로토타입입니다.
`data/chunks.json`의 근거 문서는 실제 원문이 아닌 **데모용 예시 텍스트**입니다.

## 실행 방법

```bash
cd finbridge_demo
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env
# .env 파일 열어서 GEMINI_API_KEY=발급받은키 로 수정

streamlit run app.py
```

## 구조

- `data/chunks.json` — 데모용 근거 문서 조각 (B 3개 + C 4개)
- `schemas.py` — 추출/답변 Pydantic 스키마
- `pipeline.py` — 추출 → 근거 선택(키워드 매칭) → 답변 생성 → 간이 검증
- `app.py` — Streamlit UI, 6개 예시 버튼 포함

## 다음 단계 (본 MVP로 확장 시)

- `data/chunks.json`을 실제 PDF에서 발췌한 원문 + 실제 출처 URL로 교체
- BM25 + 다국어 임베딩 기반 하이브리드 검색으로 `select_chunks` 대체
- 시나리오 A(일반 질문) 추가
- 평가셋 80개로 정량 평가
