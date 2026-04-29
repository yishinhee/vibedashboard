"""
uiux개선.md 파서 — ImprovementItem / ChecklistItem 추출.

`### [P{n}] 제목` / `### ✅ [P{n}] 제목` 헤딩 → ImprovementItem.
`### Phase {n}` 헤딩 아래 `- ✅` / `- [x]` / `- [ ]` → ChecklistItem.
Phase 가 없으면 stub 으로 get_or_create (design_parser 가 나중에 보강).
"""
from __future__ import annotations

import re
from typing import Any

from apps.dashboard.models import ChecklistItem, ImprovementItem, Phase
from apps.parsers.services.base_parser import BaseParser

IMPROVEMENT_HEADING = re.compile(r"^###\s+(✅\s+)?\[(P[0-3])\]\s+(.+?)\s*$")
PHASE_HEADING = re.compile(r"^###\s+Phase\s+(\d+)\s*[—\-:]?\s*(.*)$")
CHECK_DONE = re.compile(r"^[\-\*]\s+(?:✅|\[[xX]\])\s+(.+)$")
CHECK_TODO = re.compile(r"^[\-\*]\s+\[\s\]\s+(.+)$")


class ImprovementParser(BaseParser):
    filename = "uiux개선.md"

    def parse(self, text: str) -> dict[str, Any]:
        improvements: list[dict] = []
        phase_items: dict[int, dict] = {}
        current_phase: int | None = None
        current_imp: dict | None = None

        for raw_line in text.splitlines():
            line = raw_line.rstrip()

            m_imp = IMPROVEMENT_HEADING.match(line)
            if m_imp:
                current_imp = {
                    "priority": m_imp.group(2),
                    "title": m_imp.group(3),
                    "is_done": bool(m_imp.group(1)),
                    "description": "",
                    "raw_text": raw_line,
                }
                improvements.append(current_imp)
                current_phase = None
                continue

            m_phase = PHASE_HEADING.match(line)
            if m_phase:
                current_phase = int(m_phase.group(1))
                phase_items.setdefault(current_phase, {
                    "name": m_phase.group(2).strip().lstrip("—-").strip(),
                    "items": [],
                })
                current_imp = None
                continue

            if line.startswith("#"):
                current_imp = None

            if current_phase is not None:
                m_done = CHECK_DONE.match(line)
                m_todo = CHECK_TODO.match(line)
                if m_done:
                    phase_items[current_phase]["items"].append({
                        "content": m_done.group(1).strip(),
                        "is_done": True,
                        "raw_text": raw_line,
                    })
                    continue
                if m_todo:
                    phase_items[current_phase]["items"].append({
                        "content": m_todo.group(1).strip(),
                        "is_done": False,
                        "raw_text": raw_line,
                    })
                    continue

            if current_imp is not None and line.strip() and not line.startswith("#"):
                if current_imp["description"]:
                    current_imp["description"] += "\n"
                current_imp["description"] += line.strip()

        return {"improvements": improvements, "phase_items": phase_items}

    def save(self, project, parsed: dict[str, Any]) -> str:
        ImprovementItem.objects.filter(project=project).delete()
        ChecklistItem.objects.filter(project=project).delete()

        ImprovementItem.objects.bulk_create([
            ImprovementItem(
                project=project,
                priority=imp["priority"],
                title=imp["title"],
                description=imp["description"],
                is_done=imp["is_done"],
                raw_text=imp["raw_text"],
            )
            for imp in parsed["improvements"]
        ])

        check_count = 0
        for phase_num, info in parsed["phase_items"].items():
            phase, _ = Phase.objects.get_or_create(
                project=project,
                phase_num=phase_num,
                defaults={"name": info["name"]},
            )
            ChecklistItem.objects.bulk_create([
                ChecklistItem(
                    phase=phase,
                    project=project,
                    content=item["content"],
                    is_done=item["is_done"],
                    raw_text=item["raw_text"],
                )
                for item in info["items"]
            ])
            check_count += len(info["items"])

            phase.total_items = len(info["items"])
            phase.done_items = sum(1 for it in info["items"] if it["is_done"])
            if phase.total_items > 0 and phase.done_items == phase.total_items:
                phase.status = Phase.Status.DONE
            elif phase.done_items > 0:
                phase.status = Phase.Status.IN_PROGRESS
            phase.save(update_fields=["total_items", "done_items", "status"])

        return f"개선 {len(parsed['improvements'])}건, 체크리스트 {check_count}건"
