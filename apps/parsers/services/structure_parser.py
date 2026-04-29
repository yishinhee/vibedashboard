"""
프로그램구조.md 파서 — AppModule / ModelInfo 추출.

앱 헤딩(`## N. apps/<name>/`)을 만나면 AppModule 시작.
하위 `### 모델` / `### 서비스` 섹션에서 모델·서비스 수 집계.
"""
from __future__ import annotations

import re
from typing import Any

from apps.dashboard.models import AppModule, ModelInfo
from apps.parsers.services.base_parser import BaseParser

APP_HEADING = re.compile(r"^##\s+\d+\.\s+apps/([\w_]+)/?\s*[—\-:]?\s*(.*)$")
MODEL_CLASS = re.compile(r"^class\s+([A-Z]\w*)")
SERVICE_DEF = re.compile(r"^def\s+(\w+)")
SERVICE_HEADER_NAMES = {"함수", "함수명", "명령어", "url", "name", "뷰"}


def _table_cells(line: str) -> list[str]:
    cells = [c.strip().strip("`").strip() for c in line.split("|")]
    return [c for c in cells if c != ""]


def _is_separator(line: str) -> bool:
    return line.startswith("|") and set(line.replace("|", "").strip()) <= {"-", ":"}


class StructureParser(BaseParser):
    filename = "프로그램구조.md"

    def parse(self, text: str) -> dict[str, Any]:
        apps: dict[str, dict] = {}
        current = None
        section: str | None = None
        in_code = False

        for raw_line in text.splitlines():
            line = raw_line.rstrip()
            stripped = line.strip()

            m_app = APP_HEADING.match(stripped)
            if m_app:
                current = m_app.group(1)
                apps.setdefault(current, {
                    "responsibility": m_app.group(2).strip().lstrip("—-").strip(),
                    "model_count": 0,
                    "service_count": 0,
                    "raw_text": raw_line,
                    "models": {},
                })
                section = None
                continue

            if stripped.startswith("```"):
                in_code = not in_code
                continue

            if stripped.startswith("### "):
                if "모델" in stripped:
                    section = "model"
                elif "서비스" in stripped or "관리 명령어" in stripped:
                    section = "service"
                else:
                    section = None
                continue

            if current is None:
                continue

            if in_code:
                m_class = MODEL_CLASS.match(stripped)
                if m_class:
                    name = m_class.group(1)
                    apps[current]["models"].setdefault(name, {
                        "model_name": name, "table_name": "", "fields": "",
                    })
                    continue
                m_def = SERVICE_DEF.match(stripped)
                if m_def:
                    apps[current]["service_count"] += 1
                continue

            if not stripped.startswith("|") or _is_separator(stripped):
                continue

            cells = _table_cells(stripped)
            if not cells:
                continue

            if section == "model":
                first = cells[0]
                if re.match(r"^[A-Z]\w+$", first) and first.lower() not in {"모델", "model"}:
                    apps[current]["models"].setdefault(first, {
                        "model_name": first,
                        "table_name": cells[1] if len(cells) > 1 else "",
                        "fields": cells[2] if len(cells) > 2 else "",
                    })
            elif section == "service":
                first = cells[0]
                if first.lower() in SERVICE_HEADER_NAMES:
                    continue
                apps[current]["service_count"] += 1

        for info in apps.values():
            info["model_count"] = len(info["models"])

        return {"apps": apps}

    def save(self, project, parsed: dict[str, Any]) -> str:
        AppModule.objects.filter(project=project).delete()
        ModelInfo.objects.filter(project=project).delete()

        app_rows = []
        model_rows = []
        for app_name, info in parsed["apps"].items():
            app_rows.append(AppModule(
                project=project,
                app_name=app_name,
                responsibility=info["responsibility"],
                model_count=info["model_count"],
                service_count=info["service_count"],
                raw_text=info["raw_text"],
            ))
            for m in info["models"].values():
                model_rows.append(ModelInfo(
                    project=project,
                    app_name=app_name,
                    model_name=m["model_name"],
                    table_name=m["table_name"],
                    fields=m["fields"],
                ))

        AppModule.objects.bulk_create(app_rows)
        ModelInfo.objects.bulk_create(model_rows)

        return f"앱 {len(app_rows)}건, 모델 {len(model_rows)}건"
