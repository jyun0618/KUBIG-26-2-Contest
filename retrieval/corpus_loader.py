from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Optional

from retrieval.category_map import category_to_scenario

DATA_DIR = Path(__file__).parent.parent / "data"
RETRIEVER_DATASET_DIR = DATA_DIR / "Retriever_dataset"
DOCUMENTS_PATH = RETRIEVER_DATASET_DIR / "documents" / "documents.jsonl"
SOURCE_FILE_MAP_PATH = RETRIEVER_DATASET_DIR / "metadata" / "source_file_map.json"
DEFAULT_CHUNK_VERSION = "chunk_400_60"


def _read_jsonl(path: Path) -> List[dict]:
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def _load_eval_source_file_map() -> Dict[str, Optional[str]]:
    """평가셋 evidence.source_file과 매칭하기 위한 doc_id -> 원본 파일명 매핑.

    PDF 문서는 documents.jsonl의 source_file과 동일하지만, Web 문서는
    documents.jsonl에서 source_file이 항상 null이라 별도 매핑이 필요하다
    (metadata/source_file_map.json 참고 — 유한의 평가셋이 이 파일명 기준으로
    근거를 인용함, 실제 eval jsonl과 대조해서 확인함).
    """
    with open(SOURCE_FILE_MAP_PATH, encoding="utf-8") as f:
        mapping = json.load(f)
    mapping.pop("_notice", None)
    return mapping


def load_real_corpus(chunk_version: str = DEFAULT_CHUNK_VERSION) -> List[dict]:
    """병현의 실제 코퍼스(chunks.jsonl + documents.jsonl)를 읽어서
    기존 pipeline.py/retrieval 코드가 기대하는 chunk 스키마로 정규화한다.

    정규화 이유: BM25Index/DenseIndex/HybridRetriever/generate_answer는 모두
    institution/document_title/scenario/published_at 같은 필드명을 쓰도록
    이미 짜여 있고(placeholder data/chunks.json 기준), 실제 코퍼스는 organization/
    title/category처럼 다른 이름을 쓴다. 필드명을 여기서 한 번에 맞춰주면
    나머지 코드는 전혀 손댈 필요가 없다.
    """
    documents = _read_jsonl(DOCUMENTS_PATH)
    doc_by_id = {d["id"]: d for d in documents}
    eval_source_file_by_id = _load_eval_source_file_map()

    chunks_path = RETRIEVER_DATASET_DIR / "chunks" / chunk_version / "chunks.jsonl"
    raw_chunks = _read_jsonl(chunks_path)

    normalized: List[dict] = []
    for c in raw_chunks:
        doc = doc_by_id.get(c["doc_id"], {})
        normalized.append(
            {
                "id": c["chunk_id"],
                "doc_id": c["doc_id"],
                "scenario": category_to_scenario(c["category"]),
                "institution": c["organization"],
                "document_title": c["title"],
                "language": c["language"],
                "topic": c["category"],
                "published_at": doc.get("retrieved_at"),
                "page": None,  # chunk 단계에는 페이지 정보가 없음 — 평가 매칭은 문서+근거문장 텍스트로 수행
                "source_url": c.get("source_url"),
                "source_file": eval_source_file_by_id.get(c["doc_id"]),
                "text": c["text"],
            }
        )
    return normalized
