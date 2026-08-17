from __future__ import annotations

import math
import re
from difflib import SequenceMatcher
from typing import List, Optional

_PUNCT_RE = re.compile(r"[\s\.,;:!?'\"“”‘’()\[\]{}·\-​]")


def _normalize(text: Optional[str]) -> str:
    if not text:
        return ""
    return _PUNCT_RE.sub("", text).lower()


def _text_matches(evidence: str, chunk_text: str, min_ratio: float = 0.6) -> bool:
    """근거 문장이 chunk 텍스트 안에 (거의) 포함되는지 판정.

    정확히 포함되면 바로 True. chunk 경계 때문에 문장이 살짝 잘린 경우를 대비해
    최장 공통 부분열 길이가 근거 문장의 min_ratio 이상이면 매칭으로 인정한다.
    """
    ev = _normalize(evidence)
    ct = _normalize(chunk_text)
    if not ev:
        return False
    if ev in ct:
        return True
    match = SequenceMatcher(None, ev, ct).find_longest_match(0, len(ev), 0, len(ct))
    return (match.size / len(ev)) >= min_ratio


def _document_matches(gold: dict, chunk: dict) -> bool:
    gold_file = gold.get("source_file")
    chunk_file = chunk.get("source_file")
    gold_url = gold.get("source_url")
    chunk_url = chunk.get("source_url")

    if gold_file and chunk_file:
        # 실제 평가셋(evidence.source_file)과 실제 코퍼스(chunk.source_file, corpus_loader가 채움)는
        # 둘 다 원본 파일명을 갖고 있어 가장 정확한 매칭 키다.
        doc_ok = gold_file == chunk_file
    elif gold_url and chunk_url:
        doc_ok = gold_url == chunk_url
    else:
        gold_title = gold.get("source_title", gold.get("document_title"))
        doc_ok = _normalize(gold.get("institution")) == _normalize(chunk.get("institution")) and _normalize(
            gold_title
        ) == _normalize(chunk.get("document_title"))

    gold_page = gold.get("page")
    chunk_page = chunk.get("page")
    if gold_page is not None and chunk_page is not None:
        doc_ok = doc_ok and gold_page == chunk_page

    return doc_ok


def is_relevant(chunk: dict, gold_item: dict) -> bool:
    """평가셋 정답(근거 문장 + 문서(+URL) + 페이지)과 검색된 chunk가 같은 근거를 가리키는지 판정.

    chunk_id를 쓰지 않는 이유는 설계안 06번 섹션 참고 — chunk_id는 청킹 설정에
    종속적인 구현 디테일이라 평가셋에 못박지 않기로 팀에서 결정함(Slack).
    """
    evidence_text = gold_item.get("quote", gold_item.get("evidence_sentence", ""))
    return _document_matches(gold_item, chunk) and _text_matches(evidence_text, chunk["text"])


def _relevance_vector(retrieved: List[dict], gold_list: List[dict]) -> List[int]:
    return [1 if any(is_relevant(c, g) for g in gold_list) else 0 for c in retrieved]


def recall_at_k(retrieved: List[dict], gold_list: List[dict]) -> float:
    """top-k 안에 정답이 하나라도 있으면 1.0, 없으면 0.0."""
    return 1.0 if sum(_relevance_vector(retrieved, gold_list)) > 0 else 0.0


def mrr_at_k(retrieved: List[dict], gold_list: List[dict]) -> float:
    """가장 먼저 등장하는 정답의 순위(1-indexed)의 역수. 못 찾으면 0."""
    rel = _relevance_vector(retrieved, gold_list)
    for rank, r in enumerate(rel, start=1):
        if r:
            return 1.0 / rank
    return 0.0


def ndcg_at_k(retrieved: List[dict], gold_list: List[dict]) -> float:
    """이진 관련성 기준 nDCG. 정답이 여러 개일 때 상위 배치를 더 엄격히 평가."""
    rel = _relevance_vector(retrieved, gold_list)
    dcg = sum(r / math.log2(i + 2) for i, r in enumerate(rel))
    ideal_hits = min(len(gold_list), len(retrieved))
    idcg = sum(1.0 / math.log2(i + 2) for i in range(ideal_hits))
    return dcg / idcg if idcg > 0 else 0.0
