import json
import os
import re
from pathlib import Path
from typing import List

from google import genai
from google.genai import types

from schemas import ExtractionResult, StructuredAnswer

DATA_PATH = Path(__file__).parent / "data" / "chunks.json"
MODEL_NAME = "gemini-2.0-flash"

_STOPWORDS = {"the", "a", "an", "is", "are", "to", "of", "and", "or", "이", "가", "을", "를", "은", "는", "의", "에", "에서"}

_client = None


def _get_client() -> genai.Client:
    global _client
    if _client is None:
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            raise RuntimeError("GEMINI_API_KEY 환경변수가 설정되어 있지 않습니다. .env 또는 export로 설정하세요.")
        _client = genai.Client(api_key=api_key)
    return _client


def load_chunks() -> List[dict]:
    with open(DATA_PATH, encoding="utf-8") as f:
        return json.load(f)["chunks"]


def _tokenize(text: str) -> set:
    words = re.findall(r"[가-힣]+|[A-Za-z]+", text.lower())
    return {w for w in words if w not in _STOPWORDS and len(w) > 1}


def select_chunks(scenario: str, user_text: str, top_k: int = 4) -> List[dict]:
    chunks = [c for c in load_chunks() if c["scenario"] == scenario]
    query_tokens = _tokenize(user_text)
    scored = []
    for c in chunks:
        chunk_tokens = _tokenize(c["text"])
        overlap = len(query_tokens & chunk_tokens)
        scored.append((overlap, c))
    scored.sort(key=lambda x: x[0], reverse=True)
    selected = [c for _, c in scored[:top_k]]
    if not selected:
        selected = chunks[:top_k]
    return selected


def extract_info(user_text: str) -> ExtractionResult:
    client = _get_client()
    prompt = f"""다음은 외국인 체류자가 입력한 금융 안내문 또는 메시지입니다. 아래 JSON 스키마에 맞춰 핵심 정보를 추출하세요.
scenario는 안내문/공지/조건 설명이면 "guidance", 문자메시지/의심스러운 연락이면 "suspicious_message"로 분류하세요.
확실하지 않은 필드는 빈 리스트로 두고, 원문에 없는 내용을 추측해서 채우지 마세요.

입력:
\"\"\"{user_text}\"\"\"
"""
    resp = client.models.generate_content(
        model=MODEL_NAME,
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=ExtractionResult,
        ),
    )
    return ExtractionResult.model_validate_json(resp.text)


def generate_answer(user_text: str, extraction: ExtractionResult, chunks: List[dict]) -> StructuredAnswer:
    client = _get_client()
    sources_block = "\n\n".join(
        f"[{c['id']}] {c['institution']} - {c['document_title']} ({c['published_at']})\n{c['text']}"
        for c in chunks
    )
    prompt = f"""당신은 국내 체류 외국인을 돕는 금융 정보 안내 Agent입니다.
금융상품을 추천하거나 가입 가능 여부를 단정하지 않습니다. 사기 여부도 "확정"하지 않고 위험 신호와 근거만 설명합니다.
아래 "공식 근거"에 없는 내용은 답변에 포함하지 말고, 확인이 필요한 사항은 unconfirmed에 넣으세요.

[사용자 입력]
{user_text}

[추출된 정보]
{extraction.model_dump_json(indent=2)}

[공식 근거 (스니펫)]
{sources_block}

위 스키마(situation_summary, plain_explanation, key_info, risk_signals, do_now, do_not, sources, unconfirmed)에 맞춰 한국어로 답변을 작성하세요.
sources 필드에는 위 근거의 "기관명 - 문서명 (발행일)" 형식으로 실제로 답변에 사용한 것만 넣으세요.
guidance 시나리오면 risk_signals는 비워도 됩니다. suspicious_message 시나리오면 risk_signals를 반드시 채우세요.
"""
    resp = client.models.generate_content(
        model=MODEL_NAME,
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=StructuredAnswer,
        ),
    )
    return StructuredAnswer.model_validate_json(resp.text)


def verify_answer(answer: StructuredAnswer, chunks: List[dict]) -> List[str]:
    """아주 단순한 검증: key_info에 등장하는 숫자가 근거 chunk 원문에도 등장하는지 확인."""
    combined_source_text = " ".join(c["text"] for c in chunks)
    warnings = []
    number_pattern = re.compile(r"\d+(?:[.,]\d+)?\s*(?:%|달러|원|일|만원|USD)?")
    for item in answer.key_info:
        for match in number_pattern.findall(item):
            digits = re.sub(r"[^\d]", "", match)
            if len(digits) >= 2 and digits not in combined_source_text.replace(",", ""):
                warnings.append(f"'{item}' 안의 숫자 '{match}'가 근거 원문에서 그대로 확인되지 않았습니다.")
    return warnings


def run_pipeline(user_text: str) -> dict:
    extraction = extract_info(user_text)
    chunks = select_chunks(extraction.scenario, user_text)
    answer = generate_answer(user_text, extraction, chunks)
    warnings = verify_answer(answer, chunks)
    return {
        "extraction": extraction,
        "chunks": chunks,
        "answer": answer,
        "verification_warnings": warnings,
    }
