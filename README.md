# FinBridge Korea

국내 체류 외국인이 금융기관·공공기관 안내문(시나리오 B) 또는 의심 문자(시나리오 C)를
입력하면, 실제 공식 문서 코퍼스 기반 BM25+Dense 하이브리드 검색으로 근거를 찾아
핵심 조건·위험 신호를 추출하고 "지금 할 일 / 하지 말아야 할 일"을 제시하는 프로토타입입니다.

## 실행 방법

```bash
cd finbridge_chatbot
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env
# .env 파일 열어서 GEMINI_API_KEY=발급받은키 로 수정

streamlit run app.py
```

## 구조

- `data/Retriever_dataset/` — 실제 공식문서 코퍼스(21개 문서, chunk 버전 3종) + 통계/중복 메타데이터. 팀 공유용 최종 산출물
- `data/rag_evaluation_dataset.jsonl` — 검색 성능 평가셋 (120문항, ko/en)
- `schemas.py` — 추출/답변 Pydantic 스키마
- `retrieval/` — BM25(`bm25s`) + Dense(`gemini-embedding-001`) 하이브리드 검색 모듈: RRF fusion, 리랭커, 한국어 토크나이저(`kiwipiepy`), 쿼리 번역
- `pipeline.py` — 추출 → 하이브리드 검색으로 근거 선택 → 답변 생성(`gemini-3.6-flash`) → 간이 검증
- `eval/` — 검색 성능 평가 스크립트 (BM25/Dense/Hybrid 비교, Recall@k·MRR@k·nDCG@k, 언어별 breakdown)
- `app.py` — Streamlit UI, 6개 예시 버튼 포함

## 검색 성능 평가 실행

```bash
python -m eval.run_retrieval_eval --eval-set data/rag_evaluation_dataset.jsonl --split validation
```

## 다음 단계

- 시나리오 A(일반 질문) 추가
- 검색 단계뿐 아니라 최종 답변 생성 단계의 정성/정량 평가
