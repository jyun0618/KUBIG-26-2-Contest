from __future__ import annotations

import re
from typing import List

from kiwipiepy import Kiwi

_kiwi = Kiwi()

# 명사류(NNG/NNP/NNB/NR) + 외래어/한자(SL/SH) + 숫자(SN)만 남긴다.
# 조사/어미/동사 활용형은 BM25 토큰으로 부적합하므로 제외.
_KEEP_TAGS = {"NNG", "NNP", "NNB", "NR", "SL", "SH", "SN"}

_EN_STOPWORDS = {
    "the", "a", "an", "is", "are", "was", "were", "to", "of", "and", "or",
    "in", "on", "for", "with", "this", "that", "do", "does", "did", "can",
    "how", "what", "when", "where", "i", "my", "me",
}


def tokenize(text: str) -> List[str]:
    """한국어 형태소 분석 + 영문/숫자 토큰을 합쳐 BM25용 토큰 리스트를 만든다."""
    tokens: List[str] = []
    for t in _kiwi.tokenize(text):
        if t.tag in _KEEP_TAGS and len(t.form) > 1:
            tokens.append(t.form.lower())

    for word in re.findall(r"[A-Za-z0-9][A-Za-z0-9\-]*", text):
        lowered = word.lower()
        if lowered not in _EN_STOPWORDS and len(lowered) > 1:
            tokens.append(lowered)

    return tokens


def contains_hangul(text: str) -> bool:
    return bool(re.search(r"[가-힣]", text))
