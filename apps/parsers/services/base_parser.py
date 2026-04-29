"""
파서 추상 클래스 — 모든 파일별 파서가 상속한다.

agents.md §파싱 정책:
- 외부 파일은 read-only. 어떤 경우에도 쓰지 않는다 (open(..., 'w'), os.remove 등 금지).
- 파싱 실패는 예외 throw 가 아니라 raw_text 에 원문 저장 + 요약에 실패 건수 누적.
- 트랜잭션 범위 내에서 기존 row 삭제 → 새 row 일괄 저장 (재진입 안전).
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any

from django.db import transaction

if TYPE_CHECKING:
    from apps.projects.models import Project


class BaseParser(ABC):
    """문서 파서 추상 인터페이스.

    하위 클래스는 다음을 구현한다:
    - 클래스 속성 ``filename``: 대상 파일명 (예: ``"기능정의.md"``)
    - ``parse(text)`` : 텍스트를 구조화 dict 로 변환 (DB 미접근, 순수 함수)
    - ``save(project, parsed)`` : dict 를 ORM 으로 저장하고 요약 문자열 반환

    호출자(``sync_service``) 는 ``parse_and_save`` 만 호출한다.
    """

    filename: str = ""

    @abstractmethod
    def parse(self, text: str) -> dict[str, Any]:
        """텍스트만 받아 파싱한 dict 를 반환. DB 접근 금지."""
        raise NotImplementedError

    @abstractmethod
    def save(self, project: "Project", parsed: dict[str, Any]) -> str:
        """``parse`` 결과를 DB 에 저장하고 요약 문자열 반환.

        형식 예: ``"SCR 7건, F 22건"`` / ``"FeatureMap 22건"``.
        """
        raise NotImplementedError

    @transaction.atomic
    def parse_and_save(self, project: "Project", text: str) -> str:
        """sync_service 진입점 — parse → save 를 하나의 트랜잭션으로 묶는다."""
        parsed = self.parse(text)
        return self.save(project, parsed)
