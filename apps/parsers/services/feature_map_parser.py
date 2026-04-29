"""
feature_map.md 파서 — FeatureMap 추출.

표 행 첫 셀이 F-* 인 행을 매핑 행으로 인식한다.
컬럼: feature_id / feature_name / entry_point / view_handler / service / model_db / template_ui / external_api.
"""
from __future__ import annotations

import re
from typing import Any

from apps.dashboard.models import FeatureMap
from apps.parsers.services.base_parser import BaseParser

F_PATTERN = re.compile(r"^F-[A-Z0-9_-]+$")


def _row_cells(line: str) -> list[str]:
    cells = [c.strip() for c in line.split("|")]
    if cells and cells[0] == "":
        cells = cells[1:]
    if cells and cells[-1] == "":
        cells = cells[:-1]
    return cells


def _strip_md(s: str) -> str:
    return s.strip("`").strip()


def _safe(cells: list[str], idx: int) -> str:
    return _strip_md(cells[idx]) if 0 <= idx < len(cells) else ""


def _is_separator(line: str) -> bool:
    return line.startswith("|") and set(line.replace("|", "").strip()) <= {"-", ":"}


class FeatureMapParser(BaseParser):
    filename = "feature_map.md"

    def parse(self, text: str) -> dict[str, Any]:
        rows: dict[str, dict] = {}

        for raw_line in text.splitlines():
            line = raw_line.strip()
            if not line.startswith("|") or _is_separator(line):
                continue

            cells = _row_cells(line)
            if not cells:
                continue

            first = _strip_md(cells[0])
            if not F_PATTERN.match(first):
                continue

            if first in rows:
                continue

            rows[first] = {
                "feature_id": first,
                "feature_name": _safe(cells, 1),
                "entry_point": _safe(cells, 2),
                "view_handler": _safe(cells, 3),
                "service": _safe(cells, 4),
                "model_db": _safe(cells, 5),
                "template_ui": _safe(cells, 6),
                "external_api": _safe(cells, 7),
                "raw_text": raw_line,
            }

        return {"rows": list(rows.values())}

    def save(self, project, parsed: dict[str, Any]) -> str:
        FeatureMap.objects.filter(project=project).delete()
        FeatureMap.objects.bulk_create([
            FeatureMap(project=project, **r) for r in parsed["rows"]
        ])
        return f"FeatureMap {len(parsed['rows'])}건"
