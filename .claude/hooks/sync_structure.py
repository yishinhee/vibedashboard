"""
PostToolUse Hook v3 — 변경 성격 분류 + feature_map.md 갱신 게이트.

동작 흐름:
  [코드 파일 수정]
    → 변경 성격 분류 (단순/기능변경/신규)
    → 기능변경·신규 시 tmp/pending_updates.json 에 항목 추가
    → "feature_map.md 갱신 전 다음 작업 금지" 출력

  [feature_map.md 수정]
    → tmp/pending_updates.json 에서 해당 항목 클리어
    → "feature_map.md 갱신 확인됨" 출력

  [프로그램구조.md 수정]
    → tmp/pending_updates.json 에서 structure 항목 클리어

세션 종료 시 dod_check.py 가 pending_updates.json 잔여 항목 블로킹.
"""

import json
import os
import sys
from datetime import datetime

_HOOK_DIR     = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.abspath(os.path.join(_HOOK_DIR, "..", ".."))
_PENDING_JSON = os.path.join(_PROJECT_ROOT, "tmp", "pending_updates.json")

CODE_EXTS    = {".py", ".html", ".js", ".ts", ".css"}
DOC_SKIP     = {"docs/", ".claude/", "migrations/", "__pycache__", "venv/", "node_modules/"}

FEATURE_SIGNALS = ["/views.py", "/services/", "/urls.py", "/serializers.py", "/forms.py", "/models.py"]
NEW_SIGNALS     = ["/views.py", "/urls.py", "/services/"]


# ── pending_updates.json 관리 ─────────────────────────────────

def _load_pending() -> dict:
    if not os.path.exists(_PENDING_JSON):
        return {}
    try:
        with open(_PENDING_JSON, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def _save_pending(data: dict):
    os.makedirs(os.path.join(_PROJECT_ROOT, "tmp"), exist_ok=True)
    with open(_PENDING_JSON, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def _add_pending(source_file: str, change_type: str, required_docs: list[str]):
    """미갱신 항목 추가."""
    pending = _load_pending()
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    pending[source_file] = {
        "type": change_type,
        "time": now,
        "required_docs": required_docs,   # 갱신해야 할 문서 목록
        "cleared_docs":  [],              # 갱신 완료된 문서 목록
    }
    _save_pending(pending)


def _clear_doc_from_pending(doc_name: str):
    """특정 문서가 갱신됐을 때 pending 에서 해당 항목 클리어."""
    pending = _load_pending()
    if not pending:
        return 0

    cleared_count = 0
    to_remove = []

    for src_file, info in pending.items():
        required = info.get("required_docs", [])
        cleared  = info.get("cleared_docs", [])

        # 이 문서가 required 에 포함되면 cleared 로 이동
        matched = [d for d in required if doc_name in d]
        if matched:
            for m in matched:
                if m not in cleared:
                    cleared.append(m)
                    cleared_count += 1
            info["cleared_docs"] = cleared

        # required 가 모두 cleared 면 항목 제거
        if set(required) <= set(cleared):
            to_remove.append(src_file)

    for k in to_remove:
        del pending[k]

    _save_pending(pending)
    return cleared_count


def _pending_summary() -> list[str]:
    """현재 미완료 항목 요약."""
    pending = _load_pending()
    lines = []
    for src, info in pending.items():
        remaining = [d for d in info["required_docs"] if d not in info["cleared_docs"]]
        if remaining:
            lines.append(f"  [{info['type'].upper()}] {src}")
            for d in remaining:
                lines.append(f"    → {d} 미갱신")
    return lines


# ── 변경 성격 분류 ────────────────────────────────────────────

def _classify(norm: str, tool_name: str) -> str:
    is_new_file = tool_name in ("Write", "Create")
    if is_new_file and any(s in norm for s in NEW_SIGNALS):
        return "new"
    if any(s in norm for s in FEATURE_SIGNALS):
        return "feature"
    return "simple"


def _required_docs(norm: str, change_type: str) -> list[str]:
    docs = []
    if change_type in ("feature", "new"):
        docs.append("docs/feature_map.md")
        docs.append("docs/프로그램구조.md")
    if change_type == "new":
        docs.append("docs/기능정의.md")
    if "/models.py" in norm:
        docs.append("docs/기능정의.md")
    return list(dict.fromkeys(docs))  # 중복 제거, 순서 유지


# ── 메인 ─────────────────────────────────────────────────────

def main():
    try:
        data = json.load(sys.stdin)
    except Exception:
        return

    tool_name = data.get("tool_name", "")
    file_path = (
        data.get("tool_input", {}).get("file_path", "")
        or data.get("tool_input", {}).get("path", "")
    )
    if not file_path:
        return

    norm = file_path.replace("\\", "/")
    fname = norm.split("/")[-1]

    # ── 문서 파일이 갱신된 경우 → pending 클리어 ────────────────
    if "docs/" in norm:
        if "feature_map" in norm:
            cleared = _clear_doc_from_pending("docs/feature_map.md")
            remaining = _pending_summary()
            if cleared > 0:
                sys.stdout.buffer.write(
                    f"[sync] ✅ feature_map.md 갱신 확인 — {cleared}개 항목 클리어\n".encode()
                )
            if remaining:
                msg = "[sync] 아직 미갱신 항목이 남아있습니다:\n" + "\n".join(remaining) + "\n"
                sys.stdout.buffer.write(msg.encode())
            else:
                sys.stdout.buffer.write(b"[sync] ✅ 모든 문서 갱신 완료\n")
            return

        if "프로그램구조" in norm:
            cleared = _clear_doc_from_pending("docs/프로그램구조.md")
            if cleared > 0:
                sys.stdout.buffer.write(
                    f"[sync] ✅ 프로그램구조.md 갱신 확인 — {cleared}개 항목 클리어\n".encode()
                )
            remaining = _pending_summary()
            if remaining:
                msg = "[sync] 아직 미갱신 항목:\n" + "\n".join(remaining) + "\n"
                sys.stdout.buffer.write(msg.encode())
            return

        if "기능정의" in norm:
            cleared = _clear_doc_from_pending("docs/기능정의.md")
            if cleared > 0:
                sys.stdout.buffer.write(
                    f"[sync] ✅ 기능정의.md 갱신 확인\n".encode()
                )
            return

        return  # 그 외 docs/ 파일은 무시

    # ── 스킵 대상 ────────────────────────────────────────────────
    if any(s in norm for s in DOC_SKIP):
        return

    ext = "." + norm.rsplit(".", 1)[-1] if "." in norm else ""
    if ext not in CODE_EXTS:
        return

    ctype = _classify(norm, tool_name)

    # ── 단순 수정 ────────────────────────────────────────────────
    if ctype == "simple":
        sys.stdout.buffer.write(
            f"[sync] {fname} — 단순수정, 문서 갱신 불필요\n".encode()
        )
        return

    # ── 기능변경 / 신규 → 게이트 설치 ───────────────────────────
    req_docs = _required_docs(norm, ctype)
    _add_pending(norm, ctype, req_docs)

    tag = "신규기능" if ctype == "new" else "기능변경"
    lines = [f"[sync] {fname} — {tag} 감지 ─────────────────────────────"]

    if ctype == "new":
        lines += [
            "  필수 갱신 1 → docs/기능정의.md      : SCR-* / F-* ID 신규 등록",
            "  필수 갱신 2 → docs/프로그램구조.md  : 새 파일·함수 섹션 추가",
            "  필수 갱신 3 → docs/feature_map.md   : 신규 기능 매핑 행 추가",
            "  필수 갱신 4 → E2E 테스트 스크립트   : 신규 시나리오 작성",
        ]
    else:
        lines += [
            "  필수 갱신 1 → docs/feature_map.md   : 기능↔파일:함수↔DB 매핑 갱신",
            "  필수 갱신 2 → docs/프로그램구조.md  : 수정된 함수·클래스 섹션 갱신",
        ]
        if "/models.py" in norm:
            lines.append("  필수 갱신 3 → docs/기능정의.md      : DB 스키마 변경 반영")
        if "/services/" in norm:
            base = fname.replace(".py", "")
            lines.append(f"  DoD 체크    → test_{base}.py 존재 여부 확인")

    lines += [
        "  ※ 위 문서 갱신 완료 후 다음 작업 진행",
        "  ※ 갱신 후 자동으로 게이트 해제됨",
    ]
    sys.stdout.buffer.write(("\n".join(lines) + "\n").encode())

    # 현재 누적된 미완료 항목도 표시
    summary = _pending_summary()
    if len(summary) > 2:
        sys.stdout.buffer.write(
            f"[sync] 현재 미갱신 누적 항목 {len([l for l in summary if l.startswith('  [')])  }개\n".encode()
        )


if __name__ == "__main__":
    main()
