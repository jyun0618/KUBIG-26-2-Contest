from typing import List, Literal, Optional

from pydantic import BaseModel, Field


class ExtractionResult(BaseModel):
    scenario: Literal["guidance", "suspicious_message"] = Field(
        description="입력이 안내문 해석인지 의심 메시지 확인인지"
    )
    language: str = Field(description="입력 언어 코드, 예: ko, en")
    institutions_mentioned: List[str] = Field(default_factory=list)
    required_documents: List[str] = Field(default_factory=list)
    amounts: List[str] = Field(default_factory=list)
    deadlines: List[str] = Field(default_factory=list)
    requested_actions: List[str] = Field(
        default_factory=list,
        description="메시지/안내문이 사용자에게 요구하는 행동 (예: 링크 클릭, 송금, 개인정보 입력, 서류 제출)",
    )
    risk_indicators: List[str] = Field(
        default_factory=list,
        description="suspicious_message인 경우에만: 기관사칭, 긴급성 조성, 송금 요구 등",
    )


class StructuredAnswer(BaseModel):
    situation_summary: str
    plain_explanation: str
    key_info: List[str]
    risk_signals: List[str]
    do_now: List[str]
    do_not: List[str]
    sources: List[str]
    unconfirmed: List[str]
