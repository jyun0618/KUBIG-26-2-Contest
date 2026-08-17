from __future__ import annotations

import time
from typing import Callable, TypeVar

from google.genai import errors

T = TypeVar("T")

_RETRYABLE_CODES = {429, 500, 502, 503, 504}


def is_daily_quota_exhausted(e: Exception) -> bool:
    """무료 티어 generate_content는 모델당 '하루' 요청 한도가 있다(예: gemini-3.6-flash 20회/일).
    이건 분당 rate limit과 달리 몇 초 기다린다고 풀리지 않으므로 재시도가 무의미하다."""
    return "PerDay" in str(e)


def call_with_retry(fn: Callable[[], T], max_retries: int = 5, delay_seconds: float = 20) -> T:
    """Gemini API 호출 래퍼. rate limit(429)이나 일시적 서버 과부하(5xx)일 때
    잠깐 쉬었다가 재시도한다. eval 스크립트처럼 짧은 시간에 요청이 몰릴 때 특히 필요.
    단, 일일 할당량 소진(429이지만 PerDay)은 재시도해도 회복되지 않으므로 즉시 올린다."""
    for attempt in range(max_retries):
        try:
            return fn()
        except errors.APIError as e:
            if is_daily_quota_exhausted(e) or e.code not in _RETRYABLE_CODES or attempt == max_retries - 1:
                raise
            time.sleep(delay_seconds)
    raise RuntimeError("unreachable")
