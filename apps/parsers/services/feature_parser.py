"""
기능정의.md 파서 — Screen / Feature 추출.

표 행에서 SCR-* / F-* 가 어느 컬럼에 있든 인식. 매칭 실패 행은 무시,
매칭 성공 행은 raw_text 에 원문 보존(agents.md §파싱 정책).
"""
from __future__ import annotations

import re
from typing import Any

from apps.dashboard.models import Feature, Screen
from apps.parsers.services.base_parser import BaseParser

SCR_PATTERN = re.compile(r"^SCR-[A-Z0-9_-]+$")
F_PATTERN = re.compile(r"^F-[A-Z0-9_-]+$")
HEADING_PATTERN = re.compile(r"^#{2,4}\s+(.+?)\s*$")
PRIORITY_VALUES = {"P0", "P1", "P2", "P3"}
STATUS_VALUES = {"implemented", "not_implemented", "unknown"}


def _split_row(line: str) -> list[str]:
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


def _scr_in(cells: list[str]) -> str:
    for c in cells:
        cs = _strip_md(c)
        if SCR_PATTERN.match(cs):
            return cs
    return ""


def _status_in(cells: list[str]) -> str:
    for c in cells:
        cs = c.strip().lower()
        if cs in STATUS_VALUES:
            return cs
    return ""


def _priority_in(cells: list[str]) -> str:
    for c in cells:
        cs = c.strip().upper()
        if cs in PRIORITY_VALUES:
            return cs
    return ""


def _is_separator(line: str) -> bool:
    return line.startswith("|") and set(line.replace("|", "").strip()) <= {"-", ":"}


class FeatureParser(BaseParser):
    filename = "기능정의.md"

    def parse(self, text: str) -> dict[str, Any]:
        screens: dict[str, dict] = {}
        features: dict[str, dict] = {}
        current_category = ""

        for raw_line in text.splitlines():
            line = raw_line.strip()

            heading = HEADING_PATTERN.match(line)
            if heading:
                current_category = heading.group(1)
                continue

            if not line.startswith("|") or _is_separator(line):
                continue

            cells = _split_row(line)
            if not cells:
                continue

            for idx, cell in enumerate(cells):
                cell_clean = _strip_md(cell)

                if SCR_PATTERN.match(cell_clean) and cell_clean not in screens:
                    screens[cell_clean] = {
                        "screen_id": cell_clean,
                        "category": current_category,
                        "name": _safe(cells, idx + 1),
                        "url": _safe(cells, idx + 2),
                        "raw_text": raw_line,
                    }
                    break

                if F_PATTERN.match(cell_clean) and cell_clean not in features:
                    features[cell_clean] = {
                        "feature_id": cell_clean,
                        "name": _safe(cells, idx + 1),
                        "screen_id": _scr_in(cells),
                        "status": _status_in(cells) or Feature.Status.UNKNOWN,
                        "priority": _priority_in(cells),
                        "raw_text": raw_line,
                    }
                    break

        return {"screens": list(screens.values()), "features": list(features.values())}

    def save(self, project, parsed: dict[str, Any]) -> str:
        Screen.objects.filter(project=project).delete()
        Feature.objects.filter(project=project).delete()

        Screen.objects.bulk_create([
            Screen(project=project, **s) for s in parsed["screens"]
        ])
        Feature.objects.bulk_create([
            Feature(project=project, **f) for f in parsed["features"]
        ])

        return f"SCR {len(parsed['screens'])}건, F {len(parsed['features'])}건"
