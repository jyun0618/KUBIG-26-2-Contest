from __future__ import annotations

import hashlib
import os
import sys
from pathlib import Path
from typing import List, Tuple

import numpy as np
from google import genai
from google.genai import errors, types

from retrieval._retry import call_with_retry, is_daily_quota_exhausted

EMBEDDING_MODEL = "gemini-embedding-001"
CACHE_DIR = Path(__file__).parent.parent / "data" / ".cache"


def _get_client() -> genai.Client:
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY 환경변수가 설정되어 있지 않습니다. .env 또는 export로 설정하세요.")
    return genai.Client(api_key=api_key)


def _corpus_hash(chunks: List[dict]) -> str:
    payload = "\n".join(f"{c['id']}::{c['text']}" for c in chunks)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]


def _normalize(vectors: np.ndarray) -> np.ndarray:
    norms = np.linalg.norm(vectors, axis=1, keepdims=True)
    norms[norms == 0] = 1e-8
    return vectors / norms


def _embed_batch(client: genai.Client, texts: List[str], task_type: str) -> np.ndarray:
    def _call():
        resp = client.models.embed_content(
            model=EMBEDDING_MODEL,
            contents=texts,
            config=types.EmbedContentConfig(task_type=task_type),
        )
        return np.array([e.values for e in resp.embeddings], dtype=np.float32)

    vectors = call_with_retry(_call)
    return _normalize(vectors)


class DenseIndex:
    """gemini-embedding-001 임베딩 + numpy brute-force 코사인 유사도.

    코퍼스가 수백 chunk 수준이면 FAISS 같은 ANN 인덱스 없이도 충분히 빠르다
    (설계안 06번 섹션 팀 피드백 반영: 데이터셋이 작을 때 인덱싱 생략 가능).
    문서가 대규모로 늘어나면 이 클래스의 인터페이스(search)는 그대로 두고
    내부 구현만 FAISS IndexFlatIP 등으로 교체하면 된다.
    """

    def __init__(self, chunks: List[dict], cache_dir: Path = CACHE_DIR, batch_size: int = 100):
        self._ids = [c["id"] for c in chunks]
        self._client = _get_client()
        self._vectors = self._load_or_build(chunks, cache_dir, batch_size)
        self._query_cache: dict = {}  # 같은 질의가 여러 모드(dense/hybrid)에서 반복 임베딩되는 것을 방지

    def _load_or_build(self, chunks: List[dict], cache_dir: Path, batch_size: int) -> np.ndarray:
        cache_dir.mkdir(parents=True, exist_ok=True)
        digest = _corpus_hash(chunks)
        vec_path = cache_dir / f"dense_{digest}.npy"
        if vec_path.exists():
            return np.load(vec_path)

        texts = [c["text"] for c in chunks]
        if not texts:
            vectors = np.zeros((0, 0), dtype=np.float32)
        else:
            batches = []
            for i in range(0, len(texts), batch_size):
                batch = texts[i : i + batch_size]
                batches.append(_embed_batch(self._client, batch, "RETRIEVAL_DOCUMENT"))
            vectors = np.concatenate(batches, axis=0)
        np.save(vec_path, vectors)
        return vectors

    def search(self, query: str, top_k: int = 10) -> List[Tuple[str, float]]:
        """의미 유사도 기반 랭킹. 반환값은 (chunk_id, cosine_score) 내림차순 리스트."""
        if self._vectors.size == 0:
            return []
        query_vec = self._query_cache.get(query)
        if query_vec is None:
            try:
                query_vec = _embed_batch(self._client, [query], "RETRIEVAL_QUERY")[0]
            except errors.APIError as e:
                if not is_daily_quota_exhausted(e):
                    raise
                print(
                    f"[dense_index] gemini-embedding-001 일일 할당량 소진 — dense 검색 건너뜀: {query[:80]!r}",
                    file=sys.stderr,
                )
                return []
            self._query_cache[query] = query_vec
        if not np.all(np.isfinite(query_vec)):
            print(f"[dense_index] 쿼리 임베딩이 비정상(NaN/Inf)이라 dense 검색을 건너뜁니다: {query[:80]!r}", file=sys.stderr)
            return []
        scores = self._vectors @ query_vec
        k = min(top_k, len(self._ids))
        top_idx = np.argsort(-scores)[:k]
        return [(self._ids[i], float(scores[i])) for i in top_idx]
