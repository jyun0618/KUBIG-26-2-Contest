from __future__ import annotations

from typing import Dict, List, Optional

from retrieval.bm25_index import BM25Index
from retrieval.dense_index import DenseIndex
from retrieval.fusion import reciprocal_rank_fusion
from retrieval.translate import to_korean_for_bm25


class HybridRetriever:
    """BM25 + Dense를 RRF로 융합하는 검색기.

    전체 코퍼스에 대해 BM25/Dense 인덱스를 한 번만 구축해두고,
    검색 시점에 scenario 메타데이터로 후보를 필터링한다
    (코퍼스가 시나리오별로 재구축할 만큼 크지 않으므로 이 방식이 더 단순함).
    """

    def __init__(self, chunks: List[dict]):
        self._chunks_by_id: Dict[str, dict] = {c["id"]: c for c in chunks}
        self._n = len(chunks)
        self._bm25 = BM25Index(chunks)
        self._dense = DenseIndex(chunks)

    def _filter_scenario(self, ranked, scenario: Optional[str]):
        if scenario is None:
            return ranked
        return [(cid, s) for cid, s in ranked if self._chunks_by_id[cid]["scenario"] == scenario]

    def _fallback(self, scenario: Optional[str], top_k: int) -> List[dict]:
        pool = [c for c in self._chunks_by_id.values() if scenario is None or c["scenario"] == scenario]
        return pool[:top_k]

    def _to_chunks(self, ranked_ids: List[str], scenario: Optional[str], top_k: int) -> List[dict]:
        if not ranked_ids:
            return self._fallback(scenario, top_k)
        return [self._chunks_by_id[cid] for cid in ranked_ids[:top_k]]

    def retrieve_bm25_only(self, scenario: Optional[str], query: str, top_k: int = 4) -> List[dict]:
        """평가/비교 실험용: BM25 단독 랭킹."""
        if self._n == 0:
            return []
        bm25_query = to_korean_for_bm25(query)
        ranked = self._filter_scenario(self._bm25.search(bm25_query, top_k=self._n), scenario)
        return self._to_chunks([cid for cid, _ in ranked], scenario, top_k)

    def retrieve_dense_only(self, scenario: Optional[str], query: str, top_k: int = 4) -> List[dict]:
        """평가/비교 실험용: Dense 단독 랭킹."""
        if self._n == 0:
            return []
        ranked = self._filter_scenario(self._dense.search(query, top_k=self._n), scenario)
        return self._to_chunks([cid for cid, _ in ranked], scenario, top_k)

    def retrieve(
        self,
        scenario: Optional[str],
        query: str,
        top_k: int = 4,
        rrf_k: int = 60,
    ) -> List[dict]:
        if self._n == 0:
            return []

        bm25_query = to_korean_for_bm25(query)
        bm25_ranked = self._filter_scenario(self._bm25.search(bm25_query, top_k=self._n), scenario)
        dense_ranked = self._filter_scenario(self._dense.search(query, top_k=self._n), scenario)

        fused = reciprocal_rank_fusion([bm25_ranked, dense_ranked], k=rrf_k)
        return self._to_chunks([cid for cid, _score in fused], scenario, top_k)
