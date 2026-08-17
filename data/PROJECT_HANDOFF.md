# 다국어 금융 상황 이해 AI Agent — 프로젝트 인수인계 문서

작성일: 2026-08-15
목적: Retriever Dataset 구축 완료 시점의 프로젝트 인수인계 및 팀원 공유

---

## STEP 1. 현재 프로젝트 구조 요약

```
프로젝트 루트/
├── data/
│   ├── raw/pdf/                     # 원본 PDF 8개 (수정 금지)
│   ├── processed/
│   │   ├── pdf/{json,txt}/          # PDF 전처리 결과 (8개씩)
│   │   ├── web/{json,txt}/          # Web 전처리 결과 (13개씩, WEB009~013 포함)
│   │   └── corpus/                  # PDF+Web 통합 corpus
│   │       ├── json/, txt/          # 21개 문서
│   │       ├── documents.jsonl      # 21개 문서 JSONL
│   │       ├── corpus_statistics.json
│   │       ├── duplicate_report.json
│   │       ├── corpus_review.md     # corpus 적합성/Gap 분석 보고서
│   │       └── corpus_gap_analysis.json
│   └── chunks/                      # chunk 원본 작업 디렉터리
│       ├── chunk_300_50/, chunk_400_60/, chunk_500_80/
│       └── (각 폴더에 chunks.jsonl + chunk_statistics.json)
│
├── Retriever_dataset/                # ★ 팀 공유용 최종 산출물 (아래 STEP3 참고)
│   ├── README.md
│   ├── documents/documents.jsonl
│   ├── chunks/chunk_{300_50,400_60,500_80}/chunks.jsonl
│   └── metadata/ (corpus_statistics, duplicate_report, chunk_statistics × 3)
│
└── archive/                          # 작업 중 생성된 백업(삭제 아님, 보관용)
    ├── schema_backup/                # PDF/Web schema 통일 전 원본
    ├── corpus_backup/                # PDF002 필터링 전 원본
    └── web_addition_backup/          # WEB009~013 추가 전 corpus 스냅샷
```

**핵심 요약**: `data/`는 전처리 전 과정(원본→schema통일→corpus통합→chunk)이 순서대로 남아있는 작업 디렉터리이고, `Retriever_dataset/`은 그 결과물만 뽑아 정리한 배포용 폴더이며, `archive/`는 과거 버전 스냅샷 보관소입니다.

---

## STEP 2. 팀원 공유 파일 선정

### 공유 필요 (Retriever 구현 팀원)

| 파일명 | 위치 | 용도 | 공유 여부 |
|---|---|---|---|
| `documents.jsonl` | `Retriever_dataset/documents/` | 21개 문서 원문. BM25/Dense 인덱싱 기본 입력 | **필수** |
| `chunks.jsonl` (400/60) | `Retriever_dataset/chunks/chunk_400_60/` | 권장 chunk 버전. 대부분의 실험 기본값 | **필수** |
| `chunks.jsonl` (300/50, 500/80) | `Retriever_dataset/chunks/chunk_{300_50,500_80}/` | chunk size 비교 실험용 | 선택 (비교실험 하는 팀원만) |
| `README.md` | `Retriever_dataset/` | 데이터셋 요약, 폴더 구조, 추천 설정 | **필수** |
| `corpus_statistics.json` | `Retriever_dataset/metadata/` | 문서 수/언어/카테고리 분포 | **필수** |
| `duplicate_report.json` | `Retriever_dataset/metadata/` | 번역쌍 등 중복 문서 정보 (평가 설계 시 유의) | **필수** |
| `chunk_statistics_*.json` | `Retriever_dataset/metadata/` | chunk 버전별 통계 | 선택 |
| `corpus_review.md` | `data/processed/corpus/` | corpus 적합성/Gap 분석 (배경 이해용) | 선택 (신규 합류자에게 권장) |

### 공유하지 않아도 되는 파일

| 대상 | 이유 |
|---|---|
| `archive/` 전체 | 과거 스냅샷. 현재 작업에 불필요, 혼선만 유발 |
| `data/raw/pdf/` | 원본 PDF 바이너리. 용량 크고 이미 전처리 완료됨. 원문 확인이 필요한 경우에만 개별 공유 |
| `data/processed/pdf/json/`, `data/processed/web/json/` | corpus 통합 전 중간 산출물. `documents.jsonl`에 이미 반영되어 있어 중복 |
| `data/processed/pdf/txt/`, `data/processed/web/txt/` | 위와 동일한 이유로 중복 |
| `data/processed/corpus/json/`, `data/processed/corpus/txt/` | `documents.jsonl` 한 파일로 대체 가능한 개별 파일 21개 (관리 번거로움) |
| `data/chunks/` (작업 디렉터리) | `Retriever_dataset/chunks/`와 내용 동일한 중복 사본 |
| `corpus_gap_analysis.json` | 팀 전체 공유보다는 QA 담당자에게 개별 전달이 적합 (STEP4 참고) |

---

## STEP 3. Google Drive 권장 구조

Retriever_dataset 폴더를 그대로 업로드하면 됩니다(추가 가공 불필요):

```
Google Drive/
└── 다국어금융Agent_RetrieverDataset/
    ├── README.md
    ├── documents/
    │   └── documents.jsonl
    ├── chunks/
    │   ├── chunk_300_50/chunks.jsonl
    │   ├── chunk_400_60/chunks.jsonl      ← 기본 사용
    │   └── chunk_500_80/chunks.jsonl
    └── metadata/
        ├── corpus_statistics.json
        ├── duplicate_report.json
        ├── chunk_statistics_300_50.json
        ├── chunk_statistics_400_60.json
        └── chunk_statistics_500_80.json
```

- `archive/`, `data/raw/`, `data/processed/pdf|web/`는 업로드하지 않습니다.
- 참고자료로 `data/processed/corpus/corpus_review.md`(Gap 분석 보고서) 1개만 `Retriever_dataset/` 밖에 별도로 `참고자료/` 폴더를 만들어 추가하는 것을 권장합니다(QA 담당자와 신규 합류자용).
- 원본 PDF가 필요한 경우는 `data/raw/pdf/` 8개 파일만 별도 `원본문서/` 폴더로 선택적 업로드(용량 고려, 필수 아님).

---

## STEP 4. QA(Evaluation Dataset) 담당자 전달 체크리스트

### corpus 기본 정보
- [ ] 총 문서 수: **21개** (PDF 8, Web 13)
- [ ] 언어: 한국어 15, 영어 6
- [ ] Category: general_finance, bank_account(4), credit_card(3), remittance(5), foreign_exchange(2), financial_fraud(2), smishing(1), fraud_response(1)
- [ ] 사용할 파일: `Retriever_dataset/documents/documents.jsonl` (정답 근거 문장은 이 파일의 `text` 필드에서만 인용할 것)

### 어떤 문서들이 있는지 (요약)
- [ ] **계좌/카드**: PDF001(FSS 종합가이드, 한영), PDF004/005(외국인 계좌개설, EN/KO 번역쌍, 2024.08), WEB002·004·005(신용카드 종류/분실대응), WEB003(서울시 영문 계좌·카드 요약), WEB010(KB 금융거래목적확인, 2024.08)
- [ ] **송금/환전**: PDF001(Ch.V), WEB001(한국은행 환치기/상계), WEB006(해외유학생·체재자 송금 — ⚠ 방향 주의), WEB007(환전 유의사항), WEB009(하나은행 해외송금 FAQ), WEB011(WireBarley 2026 정책), WEB012(SentBe 국가별 한도표), WEB013(SentBe 환불 안내)
- [ ] **금융사기/안전**: PDF001(Ch.VI), PDF002(서울시 가이드 중 피싱 섹션만 정제), PDF006/007(서울글로벌센터 EN/KO 번역쌍), PDF008(사기예방백과사전, 2025-2026 최신, 8종 사기), PDF009(스미싱 가이드, 2015년 — ⚠ 오래됨), WEB008(보이스피싱 대처법)
- [ ] **안내문 이해**: 별도 문서군 없음 — 위 문서들의 표/조건/한도 정보를 활용해 구성해야 함 (아래 Gap 참고)

### 최신 vs 오래된 자료
- [ ] **최신**: PDF008(2025.12 발행/2026.06 개정), PDF004/005(2024.08), WEB009~013(2026, 이번에 신규 수집), WEB010(2024.08 시행 기준)
- [ ] **오래됨(주의)**: PDF009(2015년, 스미싱 기술환경 상이), PDF002(2013년 서울시 자료, 신고 전화번호 등 확인 필요), WEB001 일부 조항(개정 이력 있음 — 본문 내 "[’26.01.01 개정]" 같은 명시가 없는 조항은 최신 여부 재확인 필요)

### 남아있는 Gap (80문항 설계 시 특히 주의)
1. **안내문 실제 서식 부재**: corpus 전체가 "설명형 가이드"이며, 은행이 실제 발송하는 안내문/통지문 원본이 없음 → "안내문 이해" 20문항은 표/조건 정보를 활용한 변형 문항으로 구성해야 하며, 원래 의도한 "실제 안내문을 보고 이해" 형태는 제한적으로만 가능
2. **해외송금 방향 불일치 문서 존재**: WEB006은 "해외에 있는 한국인/장기거주자"가 대상이라 "한국 거주 외국인 → 본국 송금"과 반대 방향. 이 문서를 송금 관련 정답 근거로 쓸 때는 질문-정답 방향을 반드시 재확인할 것 (단, WEB009/WEB011/WEB012/WEB013이 이 Gap을 상당 부분 보완함)
3. **영어 corpus가 PDF001 한 문서에 편중(전체 영어 corpus 문자수의 약 90% 이상)**: 영문 질문 80문항 중 다수를 만들 경우 근거 문서가 PDF001에 쏠릴 수 있음 — 영어 문항은 PDF004/PDF006/WEB003/WEB011도 적극 활용해 균형을 맞출 것
4. **WEB002/WEB005 내용 중복**: "카드 종류" 관련 질문은 두 문서에서 거의 같은 근거 문장이 나올 수 있음 → 같은 내용으로 문항 2개를 만들지 않도록 주의
5. **외국인 카드/계좌 발급의 정량적 승인 기준 없음**: "소득이 얼마 이상이어야 카드가 나오는가" 같은 구체적 숫자 질문은 근거 문장이 없으므로 만들지 말 것 (PDF001에 정성적 설명만 존재)

### 80문항 작성 시 현실적 가능 범위 (보수적 추정)
| 영역 | 목표 | 현재 corpus로 고품질 문항 작성 가능 수 (추정) |
|---|---|---|
| 계좌·카드 | 20 | 약 14~16개 |
| 해외송금·환전 | 20 | WEB009~013 추가로 이전보다 상향, 약 13~15개 |
| 안내문 이해 | 20 | 약 8~10개 (Gap 1번 참고) |
| 금융사기·안전 | 20 | 약 18~20개 |
| **합계** | **80** | **약 53~61개** |

> 자세한 배경은 `data/processed/corpus/corpus_review.md`(Gap 분석 보고서)를 참고하세요. 해당 보고서 작성 이후 WEB009~013(송금 5건)이 추가되어 송금 영역 수치는 위 표처럼 소폭 상향 조정했습니다.

### QA 작성 시 공통 주의사항
- [ ] 정답 근거는 반드시 `documents.jsonl`의 실제 `text` 문장에서 직접 인용/paraphrase할 것 (외부 지식으로 보완 금지)
- [ ] 번역쌍 문서(PDF004↔005, PDF006↔007)는 cross-lingual 평가 문항 설계에 활용 가능 (동일 질문을 한/영 두 언어로 만들어 같은 정답 문서를 기대하는 형태)
- [ ] 오래된 문서(PDF002, PDF009)의 전화번호·URL 등은 "현재도 유효한지"와 무관하게 원문 그대로가 정답 근거이며, 임의로 최신 정보로 바꿔 질문하지 말 것

---

## STEP 5. Retriever 구현 담당자 인수인계

### 데이터 위치
- **문서 원본**: `Retriever_dataset/documents/documents.jsonl` (21 lines, 1 document per line)
- **권장 chunk**: `Retriever_dataset/chunks/chunk_400_60/chunks.jsonl` (824 chunks)
- **대안 chunk 버전**: `chunk_300_50`(1,096 chunks, 세밀), `chunk_500_80`(674 chunks, 큰 컨텍스트)

### documents.jsonl schema (10 필드, 고정 순서)
```json
{
  "id": "WEB009",
  "title": "...",
  "organization": "...",
  "language": "ko | en",
  "category": "general_finance | bank_account | credit_card | remittance | foreign_exchange | financial_fraud | smishing | fraud_response | financial_safety | other",
  "source_type": "pdf | web",
  "source_url": "실제 URL 또는 null(PDF 중 원본 URL 미확인 문서)",
  "source_file": "원본 PDF 파일명 또는 null(Web 문서는 항상 null)",
  "retrieved_at": "YYYY-MM-DD",
  "text": "원문 그대로 (요약/재작성 없음)"
}
```

### chunks.jsonl schema (9 필드, 고정 순서)
```json
{
  "chunk_id": "WEB009_0001",
  "doc_id": "WEB009",
  "title": "...",
  "organization": "...",
  "language": "...",
  "category": "...",
  "source_type": "...",
  "source_url": "...",
  "text": "chunk 단위 본문"
}
```
`chunk_id` = `{doc_id}_{4자리 zero-padded 순번}`. `text` 이외 필드는 부모 문서에서 그대로 복사.

### language / category / source_type 분포
- **language**: ko 15, en 6
- **source_type**: pdf 8, web 13 (PDF+Web 혼합 corpus, 별도 분리 없이 하나의 documents.jsonl/chunks.jsonl에 통합되어 있음 — source_type 필드로 언제든 필터링 가능)
- **category**: general_finance 3, bank_account 4, credit_card 3, remittance 5, foreign_exchange 2, financial_fraud 2, smishing 1, fraud_response 1

### Duplicate 관련 (`metadata/duplicate_report.json`)
- 실질적 중복은 **번역쌍 2세트뿐**이며 정상적 중복(제거 대상 아님): PDF004(EN)↔PDF005(KO), PDF006(EN)↔PDF007(KO)
- 이 외 문서들은 주제가 겹치더라도(예: 보이스피싱을 여러 문서가 다룸) 문장 단위 중복도가 낮음(Jaccard < 0.22, WEB009~013 추가분도 기존 문서 대비 최대 0.145로 낮음을 확인) → BM25/Dense 인덱스에서 별도 dedup 로직 없이 그대로 사용 가능

### 데이터 품질
- 21개 문서, 3개 chunk 버전(총 2,594 chunk) 전체 **valid JSON / UTF-8 검증 완료**
- chunk_id 중복 0건, 빈 text 0건
- PDF/Web 두 소스의 JSON schema는 완전히 통일되어 있어 소스별 분기 처리 불필요

### 추천 Chunk 버전과 근거

| 버전 | chunk 수 | 평균 토큰 | 특징 |
|---|---|---|---|
| 300/50 | 1,096 | 238 | 세밀한 단위. 짧은 FAQ/조항 검색에 유리하나 문맥이 잘릴 위험 ↑, 인덱스 크기 ↑ |
| **400/60 (권장)** | 824 | 313 | 문단/FAQ 1개 항목이 대체로 하나의 chunk에 담기는 균형점. 표는 헤더+데이터 일부가 overlap으로 유지됨 |
| 500/80 | 674 | 385 | 긴 컨텍스트 보존에 유리하나 chunk당 여러 주제가 섞일 가능성 ↑, dense retrieval에서 관련성 희석 위험 |

**400/60을 기본값으로 권장하는 이유**: 실제 문서 샘플(FAQ형 WEB009, 표 중심 WEB012/PDF004)을 확인한 결과, 300 토큰은 긴 FAQ 답변이나 표의 여러 행이 중간에 잘리는 경우가 상대적으로 잦고, 500 토큰은 서로 다른 Q&A 2~3개가 한 chunk에 섞이는 경우가 발생. 400/60은 이 두 극단의 중간으로, 하나의 질문-답변 또는 하나의 조건/표 단위가 chunk 경계와 대체로 일치하며 60토큰 overlap이 표 헤더나 문장 경계 유실을 상당 부분 완화함. BM25는 chunk 크기에 상대적으로 둔감하지만 Dense/Hybrid/Reranker는 chunk 길이에 성능이 민감하므로, 세 버전이 모두 준비되어 있어 실험적으로 비교 검증도 가능함.

### 알려진 주의사항
- 각 chunk 버전에서 전체의 1% 미만 비율로 `[Page 74]`처럼 페이지 마커만 담긴 초단문 chunk가 존재(문서 원문을 임의 수정하지 않기 위해 그대로 둠) — 인덱싱 시 걸러내고 싶다면 chunk 길이 하한(예: 20~30자) 필터를 추가로 적용해도 무방
- 표가 매우 긴 문서(WEB012 국가별 송금한도 28개국)는 chunk 경계에서 표 헤더가 일부 chunk에서 누락될 수 있음 — 필요 시 표 전용 chunk 전략(헤더 항상 포함)을 향후 개선 과제로 고려

---

## STEP 6. 프로젝트 현황 정리

### 현재 완료
- [x] 원본 PDF/Web 수집 (PDF 8 + Web 13, 총 21개)
- [x] PDF/Web JSON Schema 통일 (10필드 공통 schema)
- [x] Corpus 통합 (`data/processed/corpus/` — json/txt/documents.jsonl)
- [x] Corpus 품질 검토 (`corpus_review.md`, Gap 분석)
- [x] 신규 자료 5건 추가 수집 (WEB009~013, 해외송금/계좌 Gap 보완)
- [x] documents.jsonl 최종본 (21개 문서, 검증 완료)
- [x] Chunk 구축 (300/50, 400/60, 500/80 3개 버전, 총 2,594 chunk)
- [x] Chunk 통계 생성 (`chunk_statistics_*.json`)
- [x] Retriever_dataset 팀 공유 폴더 구성 (README 포함)
- [x] archive 정리 (백업 3건 이동, 원본 데이터 무손실 보존)

### 남은 작업
- [ ] BM25 인덱스 구축
- [ ] Dense Retrieval (BGE-M3 임베딩 + 벡터 인덱스/FAISS)
- [ ] Hybrid Retrieval (BM25 + Dense 결합)
- [ ] Reranker 적용 (Hybrid + Reranker)
- [ ] 평가용 QA 데이터셋 구축 (목표 80문항: 계좌/카드 20, 송금 20, 안내문 20, 금융사기 20 — 현재 corpus 기준 보수적으로 약 53~61개까지 고품질 작성 가능, 나머지는 자료 보강 후 진행 권장)
- [ ] Retrieval 성능 평가 (Recall@5, MRR@5, nDCG@5)
- [ ] 4개 Retriever 방식 비교 분석
- [ ] (선택) Streamlit 데모/시연 앱 구축
- [ ] (선택) HIGH 우선순위 추가자료 보강: 실제 안내문 서식, 외국인 카드발급 구체조건 등 (STEP7 참고)

---

## STEP 7. 최종 권고사항

### 결론: **Retriever 구현과 QA 구축을 지금 시작하는 것이 맞습니다.**

**이유**

1. **Retriever Dataset 자체의 품질은 이미 충분함.** 21개 문서, 3개 chunk 버전이 모두 UTF-8/valid JSON 검증을 통과했고, schema가 완전히 통일되어 있으며, 실질적 중복은 의도된 번역쌍 2세트뿐입니다. BM25/Dense/Hybrid/Reranker 파이프라인을 막을 기술적 결함이 없습니다.

2. **WEB009~013 추가로 가장 취약했던 Gap(외국인 관점 해외송금)이 상당 부분 보완되었습니다.** 이전 검토(`corpus_review.md`)에서 지적된 "한국 거주 외국인이 본국으로 송금"하는 시나리오 자료 부족 문제는 하나은행 FAQ, WireBarley 2026 정책, SentBe 국가별 한도표/환불 안내로 실질적으로 개선되었습니다.

3. **남은 Gap(안내문 원본 서식 부재, 카드발급 정량기준 부재)은 Retriever 개발을 막는 요인이 아니라 QA 문항 80개 중 일부(안내문 이해 영역 등)의 목표치 달성을 제약하는 요인입니다.** 즉 "Retriever가 작동하지 않을 위험"이 아니라 "80문항 중 일부 영역에서 문항 수가 목표에 못 미칠 위험"입니다. 이는 Retriever 구현과 별도로, QA 담당자가 corpus를 실제로 사용해보면서 병행 판단할 문제이지, 지금 데이터 수집을 위해 개발을 미룰 이유는 아닙니다.

4. **실제로 무엇이 부족한지는 Retriever를 최소 1회 돌려보고, QA 문항을 실제로 작성해봐야 정확히 드러납니다.** 지금 시점에서 "안내문 자료가 부족할 것 같다"는 것은 문서 검토에 기반한 추정이며, 실제 검색 결과 품질(Recall@5 등)과 QA 작성 난이도를 확인한 뒤 추가 수집 여부를 결정하는 것이 더 효율적입니다. 지금 미리 자료를 더 모으는 것은 어떤 종류의 자료가 실제로 더 필요한지 모르는 채로 수집 범위를 넓히는 것이라 비효율적일 수 있습니다.

**따라서**: 지금부터는 (1) Retriever 구현 착수, (2) 현재 corpus로 만들 수 있는 QA 문항(약 53~61개)부터 작성 착수를 병행하고, 두 작업에서 실제로 막히는 지점(특정 카테고리의 Recall이 낮다, 특정 영역 QA 근거 문장을 못 찾겠다)이 드러나면 그때 타겟을 좁혀 추가 자료를 수집하는 것을 권장합니다. 현재 시점의 선제적 추가 수집은 권장하지 않습니다.
