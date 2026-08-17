from __future__ import annotations

from typing import Dict, List, Tuple

DEFAULT_RRF_K = 60


def reciprocal_rank_fusion(
    ranked_lists: List[List[Tuple[str, float]]],
    k: int = DEFAULT_RRF_K,
) -> List[Tuple[str, float]]:
    """여러 랭킹(BM25, Dense ...)의 순위만 보고 점수를 합산해 하나의 랭킹으로 합친다.

    score(d) = sum(1 / (k + rank_i(d))) — 각 리스트에서의 등수(1부터 시작)만 쓰므로
    BM25 점수(0~수십)와 코사인 점수(0~1)처럼 스케일이 전혀 다른 두 랭킹도
    그대로 합칠 수 있다. k=60은 관례적으로 쓰이는 값이며 별도 튜닝이 거의 필요 없다.
    """
    scores: Dict[str, float] = {}
    for ranked in ranked_lists:
        for rank, (chunk_id, _score) in enumerate(ranked, start=1):
            scores[chunk_id] = scores.get(chunk_id, 0.0) + 1.0 / (k + rank)

    return sorted(scores.items(), key=lambda item: item[1], reverse=True)
