from __future__ import annotations

from typing import List, Tuple

"""bge-reranker-v2-m3 cross-encoder reranker (선택 컴포넌트).

설계안 04-⑤: Hybrid만으로 07번 섹션 평가(Recall@5/MRR@5/nDCG@5)가 충분히
잘 나오면 이 모듈은 아예 쓰지 않아도 된다. 필요해지면:

    pip install FlagEmbedding torch

를 설치하고 아래 CrossEncoderReranker를 hybrid.py의 fused 결과 상위 20개에
적용하면 된다. 무거운 의존성(torch)이라 기본 파이프라인에는 연결하지 않음.
"""


class CrossEncoderReranker:
    MODEL_NAME = "BAAI/bge-reranker-v2-m3"

    def __init__(self):
        try:
            from FlagEmbedding import FlagReranker
        except ImportError as e:
            raise ImportError(
                "reranker를 쓰려면 `pip install FlagEmbedding torch`를 먼저 설치하세요."
            ) from e
        self._model = FlagReranker(self.MODEL_NAME, use_fp16=True)

    def rerank(self, query: str, chunks: List[dict], top_k: int = 5) -> List[dict]:
        pairs = [[query, c["text"]] for c in chunks]
        scores: List[float] = self._model.compute_score(pairs)
        ranked: List[Tuple[dict, float]] = sorted(
            zip(chunks, scores), key=lambda x: x[1], reverse=True
        )
        return [c for c, _score in ranked[:top_k]]
