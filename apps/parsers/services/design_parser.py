"""
프로젝트설계.md 파서 — Phase 추출.

`## Phase {n} — 제목` 헤딩 또는 `| Phase {n} | 목표 | ...` 표 행에서 Phase 정보 추출.
status 는 헤딩/제목에 "완료/done/✅" 또는 "진행/in progress" 키워드로 판별.
improvement_parser 가 stub Phase 를 만들 수 있으므로 update_or_create 로 저장.
"""
from __future__ import annotations

import re
from typing import Any

from apps.dashboard.models import Phase
from apps.parsers.services.base_parser import BaseParser

PHASE_HEADING = re.compile(r"^##\s+Phase\s+(\d+)\s*[—\-:]?\s*(.*)$")
PHASE_TABLE_ROW = re.compile(r"^\|\s*Phase\s+(\d+)\s*\|\s*(.+?)(?:\s*\|.*)?$")


def _detect_status(text: str) -> str:
    low = text.lower()
    if "완료" in text or "✅" in text or "done" in low:
        return Phase.Status.DONE
    if "진행" in text or "in progress" in low or "in_progress" in low:
        return Phase.Status.IN_PROGRESS
    return Phase.Status.PENDING


class DesignParser(BaseParser):
    filename = "프로젝트설계.md"

    def parse(self, text: str) -> dict[str, Any]:
        phases: dict[int, dict] = {}
        current: int | None = None

        for raw_line in text.splitlines():
            line = raw_line.rstrip()
            stripped = line.strip()

            m_h = PHASE_HEADING.match(stripped)
            if m_h:
                num = int(m_h.group(1))
                rest = m_h.group(2).strip().lstrip("—-").strip()
                phases[num] = {
                    "name": rest,
                    "goal": "",
                    "status": _detect_status(stripped),
                    "raw_text": raw_line,
                }
                current = num
                continue

            m_row = PHASE_TABLE_ROW.match(stripped)
            if m_row:
                num = int(m_row.group(1))
                rest = m_row.group(2).strip().strip("`").strip()
                phases.setdefault(num, {
                    "name": rest,
                    "goal": "",
                    "status": _detect_status(stripped),
                    "raw_text": raw_line,
                })
                current = None
                continue

            if stripped.startswith("#"):
                current = None
                continue

            if current is not None and stripped:
                phases[current]["goal"] = (
                    phases[current]["goal"] + "\n" + stripped
                    if phases[current]["goal"]
                    else stripped
                )

        return {"phases": phases}

    def save(self, project, parsed: dict[str, Any]) -> str:
        for num, info in parsed["phases"].items():
            Phase.objects.update_or_create(
                project=project,
                phase_num=num,
                defaults={
                    "name": info["name"],
                    "goal": info["goal"],
                    "status": info["status"],
                },
            )
        return f"Phase {len(parsed['phases'])}건"
