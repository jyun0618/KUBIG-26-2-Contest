from __future__ import annotations

from typing import Dict, List, Tuple

import bm25s

from retrieval.tokenize_ko import tokenize


class BM25Index:
    """chunk 리스트로 BM25 인덱스를 구축하고, 쿼리로 (chunk_id, score) 랭킹을 반환한다."""

    def __init__(self, chunks: List[dict]):
        self._chunks = chunks
        self._ids = [c["id"] for c in chunks]
        corpus_tokens = [tokenize(c["text"]) for c in chunks]
        self._retriever = bm25s.BM25()
        self._retriever.index(corpus_tokens, show_progress=False)

    def search(self, query: str, top_k: int = 10) -> List[Tuple[str, float]]:
        """정확 토큰 매칭 기반 랭킹. 반환값은 (chunk_id, bm25_score) 내림차순 리스트."""
        query_tokens = tokenize(query)
        if not query_tokens:
            return []
        k = min(top_k, len(self._ids))
        if k == 0:
            return []
        results, scores = self._retriever.retrieve(
            [query_tokens], k=k, show_progress=False
        )
        ranked: List[Tuple[str, float]] = []
        for idx, score in zip(results[0], scores[0]):
            ranked.append((self._ids[int(idx)], float(score)))
        return ranked
