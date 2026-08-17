"""Retrieval 비교 평가 스크립트.

BM25 단독 / Dense 단독 / Hybrid(RRF) / Hybrid+Reranker(선택) 4가지 조합으로
Recall@k, MRR@k, nDCG@k를 계산하고 언어별(ko/en) breakdown까지 출력한다.

두 가지 평가셋 포맷을 모두 지원한다:
  - eval_set.example.json : {"items": [{"question": str, "language": str,
    "scenario": str, "gold": [...]}]} 형태의 스모크테스트용 예시.
  - data/rag_evaluation_dataset.jsonl : 유한이 실제로 만든 120문항. 레코드당
    question이 {"ko": ..., "en": ...} 두 언어를 모두 담고 있어 한 레코드가
    ko/en 두 평가 항목으로 펼쳐진다. scenario 필드가 없으므로(코퍼스의
    scenario 2분류와 평가셋 자체의 category 4분류가 서로 다른 taxonomy라
    믿을 만한 매핑이 없음) scenario=None으로 전체 코퍼스를 대상으로 검색한다
    — BM25/Dense/Hybrid 알고리즘 자체의 성능을 비교하는 게 목적이라 이쪽이
    더 정확한 비교이기도 하다.

사용법:
    python -m eval.run_retrieval_eval --eval-set eval/eval_set.example.json --top-k 5
    python -m eval.run_retrieval_eval --eval-set data/rag_evaluation_dataset.jsonl --split validation
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path
from typing import Callable, Dict, List, Optional

sys.path.insert(0, str(Path(__file__).parent.parent))

from eval.metrics import mrr_at_k, ndcg_at_k, recall_at_k
from pipeline import load_chunks
from retrieval.hybrid import HybridRetriever

MODES = ["bm25", "dense", "hybrid"]


def _load_eval_items(path: Path, split: Optional[str]) -> List[dict]:
    if path.suffix == ".jsonl":
        items = []
        with open(path, encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                rec = json.loads(line)
                if split and rec.get("split") != split:
                    continue
                for lang, question in rec["question"].items():
                    items.append(
                        {
                            "id": f"{rec['id']}_{lang}",
                            "question": question,
                            "language": lang,
                            "scenario": None,  # 코퍼스 scenario와 평가셋 category taxonomy가 달라 필터링하지 않음
                            "category": rec.get("category"),
                            "gold": rec["evidence"],
                        }
                    )
        return items

    with open(path, encoding="utf-8") as f:
        eval_set = json.load(f)
    return eval_set["items"]


def _build_modes(retriever: HybridRetriever, top_k: int, with_reranker: bool) -> Dict[str, Callable]:
    modes: Dict[str, Callable[[str, str], List[dict]]] = {
        "bm25": lambda scenario, q: retriever.retrieve_bm25_only(scenario, q, top_k=top_k),
        "dense": lambda scenario, q: retriever.retrieve_dense_only(scenario, q, top_k=top_k),
        "hybrid": lambda scenario, q: retriever.retrieve(scenario, q, top_k=top_k),
    }
    if with_reranker:
        try:
            from retrieval.reranker import CrossEncoderReranker

            reranker = CrossEncoderReranker()
            candidate_k = max(top_k * 4, 20)

            def hybrid_rerank(scenario, q):
                candidates = retriever.retrieve(scenario, q, top_k=candidate_k)
                return reranker.rerank(q, candidates, top_k=top_k)

            modes["hybrid+rerank"] = hybrid_rerank
        except ImportError as e:
            print(f"[경고] --with-reranker 지정했지만 reranker를 쓸 수 없어 건너뜁니다: {e}", file=sys.stderr)
    return modes


def run(eval_set_path: Path, top_k: int, with_reranker: bool, split: Optional[str]) -> None:
    items = _load_eval_items(eval_set_path, split)

    chunks = load_chunks()
    retriever = HybridRetriever(chunks)
    modes = _build_modes(retriever, top_k, with_reranker)

    # mode -> metric -> list[float]. breakdown_key(lang/category) -> mode -> metric -> list[float]
    overall: Dict[str, Dict[str, List[float]]] = {m: defaultdict(list) for m in modes}
    by_lang: Dict[str, Dict[str, Dict[str, List[float]]]] = defaultdict(lambda: {m: defaultdict(list) for m in modes})
    by_category: Dict[str, Dict[str, Dict[str, List[float]]]] = defaultdict(
        lambda: {m: defaultdict(list) for m in modes}
    )

    for item in items:
        question = item["question"]
        scenario = item.get("scenario")
        gold = item["gold"]
        lang = item.get("language", "unknown")
        category = item.get("category")

        for mode_name, retrieve_fn in modes.items():
            retrieved = retrieve_fn(scenario, question)
            r = recall_at_k(retrieved, gold)
            m = mrr_at_k(retrieved, gold)
            n = ndcg_at_k(retrieved, gold)
            for name, val in (("recall", r), ("mrr", m), ("ndcg", n)):
                overall[mode_name][name].append(val)
                by_lang[lang][mode_name][name].append(val)
                if category:
                    by_category[category][mode_name][name].append(val)

    def avg(vals: List[float]) -> float:
        return sum(vals) / len(vals) if vals else 0.0

    header = f"{'mode':<16}{'Recall@k':>10}{'MRR@k':>10}{'nDCG@k':>10}"
    mode_names = list(modes.keys())

    def print_table(title: str, grouped: Dict[str, Dict[str, List[float]]]) -> None:
        print(f"-- {title} (n={len(grouped[mode_names[0]]['recall'])}) --")
        print(header)
        print("-" * len(header))
        for mode_name in modes:
            r = avg(grouped[mode_name]["recall"])
            m = avg(grouped[mode_name]["mrr"])
            n = avg(grouped[mode_name]["ndcg"])
            print(f"{mode_name:<16}{r:>10.3f}{m:>10.3f}{n:>10.3f}")
        print()

    print(f"\n=== Retrieval 평가 결과 (n={len(items)}, top_k={top_k}) ===\n")
    print_table("전체", overall)

    print("=== 언어별 breakdown ===\n")
    for lang in sorted(by_lang.keys()):
        print_table(f"language = {lang}", by_lang[lang])

    if by_category:
        print("=== 카테고리별 breakdown ===\n")
        for category in sorted(by_category.keys()):
            print_table(f"category = {category}", by_category[category])


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--eval-set",
        type=Path,
        default=Path(__file__).parent / "eval_set.example.json",
        help="평가셋 JSON 경로 (기본: eval/eval_set.example.json 스모크테스트용)",
    )
    parser.add_argument("--top-k", type=int, default=5)
    parser.add_argument(
        "--with-reranker",
        action="store_true",
        help="bge-reranker-v2-m3(FlagEmbedding)가 설치되어 있으면 hybrid+rerank 열도 함께 평가",
    )
    parser.add_argument(
        "--split",
        choices=["validation", "test"],
        default="validation",
        help="jsonl 평가셋일 때만 사용. 설계 파이프라인 튜닝은 validation으로, 최종 리포트만 test로 (기본: validation)",
    )
    args = parser.parse_args()
    run(args.eval_set, args.top_k, args.with_reranker, args.split)
