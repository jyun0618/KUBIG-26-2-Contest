from __future__ import annotations

import json
import os
import sys
from pathlib import Path

from google import genai
from google.genai import errors

from retrieval._retry import call_with_retry, is_daily_quota_exhausted
from retrieval.tokenize_ko import contains_hangul

TRANSLATE_MODEL = "gemini-3.6-flash"
CACHE_PATH = Path(__file__).parent.parent / "data" / ".cache" / "translation_cache.json"

_client = None


def _load_cache() -> dict:
    if CACHE_PATH.exists():
        with open(CACHE_PATH, encoding="utf-8") as f:
            return json.load(f)
    return {}


def _save_cache() -> None:
    CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(CACHE_PATH, "w", encoding="utf-8") as f:
        json.dump(_translation_cache, f, ensure_ascii=False, indent=2)


_translation_cache: dict = _load_cache()


def _get_client() -> genai.Client:
    global _client
    if _client is None:
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            raise RuntimeError("GEMINI_API_KEY 환경변수가 설정되어 있지 않습니다.")
        _client = genai.Client(api_key=api_key)
    return _client


def to_korean_for_bm25(text: str) -> str:
    """BM25는 어휘 매칭이라 한국어 문서를 영어 질문으로 찾지 못한다.
    한글이 이미 포함된 질문은 그대로 두고, 그렇지 않을 때만 번역한다.
    (Dense 검색은 다국어 임베딩이라 이 전처리가 필요 없음 — hybrid.py에서 BM25 쪽에만 적용)

    번역 결과는 디스크에도 캐싱한다 — gemini-3.6-flash 무료 티어는 하루 요청 한도가
    있어(예: 20회/일) 같은 질문을 다음 실행에서 또 번역 시도하면 한도만 낭비된다.
    할당량이 소진된 경우에는 예외를 올리는 대신 원문을 그대로 반환해 BM25가
    (품질은 떨어지더라도) 계속 동작하게 한다.
    """
    if contains_hangul(text):
        return text
    if text in _translation_cache:
        return _translation_cache[text]

    client = _get_client()
    prompt = (
        "다음 문장을 자연스러운 한국어로 번역하세요. "
        "번역 결과만 출력하고 다른 설명은 붙이지 마세요.\n\n"
        f"{text}"
    )
    try:
        resp = call_with_retry(lambda: client.models.generate_content(model=TRANSLATE_MODEL, contents=prompt))
    except errors.APIError as e:
        if not is_daily_quota_exhausted(e):
            raise
        print(f"[translate] gemini-3.6-flash 일일 할당량 소진 — 번역 없이 원문으로 BM25 검색: {text[:80]!r}", file=sys.stderr)
        return text

    translated = (resp.text or "").strip() or text
    _translation_cache[text] = translated
    _save_cache()
    return translated
