from __future__ import annotations

"""병현의 실제 코퍼스는 category(10종)로 문서를 분류하지만, 우리 파이프라인의
Query Understanding 단계(schemas.ExtractionResult.scenario)는 guidance/
suspicious_message 2종만 구분한다. 이 매핑은 코퍼스 category를 scenario로
투영해서, extract_info()가 분류한 scenario로 코퍼스를 메타데이터 필터링할 수
있게 해준다.

주의: 이건 지윤이 정한 휴리스틱 매핑이지 팀이 합의한 것은 아니다. 사기/스미싱
관련 category만 suspicious_message로 보내고 나머지는 전부 guidance로 묶었다.
"""

SUSPICIOUS_CATEGORIES = {"financial_fraud", "smishing", "fraud_response"}


def category_to_scenario(category: str) -> str:
    return "suspicious_message" if category in SUSPICIOUS_CATEGORIES else "guidance"
