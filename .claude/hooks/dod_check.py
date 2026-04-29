"""
Stop Hook v3 — pending_updates.json 기반 DoD 블로킹.

동작:
  1. tmp/pending_updates.json 잔여 항목 확인
     → 미갱신 문서가 있으면 경고 출력 + Telegram 경고 발송
  2. 서비스 파일 수정 → 테스트 누락 체크
  3. feature_map.md 존재 여부 체크 (없으면 생성 촉구)
  4. 모든 항목 클리어 시 pending_updates.json 삭제
"""

import json
import os
import subprocess
import sys
from datetime import date

_HOOK_DIR     = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.abspath(os.path.join(_HOOK_DIR, "..", ".."))
_PENDING_JSON = os.path.join(_PROJECT_ROOT, "tmp", "pending_updates.json")
_PENDING_TG   = os.path.join(_PROJECT_ROOT, "tmp", "telegram_pending.txt")
_FEATURE_MAP  = os.path.join(_PROJECT_ROOT, "docs", "feature_map.md")


def _load_pending() -> dict:
    if not os.path.exists(_PENDING_JSON):
        return {}
    try:
        with open(_PENDING_JSON, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def _git_changed(ext=None) -> list[str]:
    files = []
    for cmd in [["git","diff","--name-only","HEAD"], ["git","diff","--name-only","--cached"]]:
        try:
            r = subprocess.run(cmd, cwd=_PROJECT_ROOT, capture_output=True, text=True, timeout=5)
            files += [f.strip() for f in r.stdout.splitlines() if f.strip()]
        except Exception:
            pass
    files = list(set(files))
    return [f for f in files if f.endswith(ext)] if ext else files


def _check_service_tests() -> list[str]:
    warns = []
    for sf in _git_changed(ext=".py"):
        if "/services/" not in sf or "test_" in sf or "migrations" in sf:
            continue
        base = os.path.basename(sf).replace(".py", "")
        found = any(
            f"test_{base}.py" in files
            for _, _, files in os.walk(_PROJECT_ROOT)
        )
        if not found:
            warns.append(f"⚠️  [DoD] 테스트 없음: {sf}\n    → test_{base}.py 작성 필요")
    return warns


def _append_telegram(warnings: list[str]):
    if os.path.exists(_PENDING_TG):
        return  # Claude 작성 pending 우선
    today = date.today().isoformat()
    text = (
        "[DoD 경고] 세션 종료 — 문서 갱신 미완료\n"
        + "\n".join(warnings)
        + f"\n작성일: {today} / 작성자: dod_check (auto)"
    )
    os.makedirs(os.path.join(_PROJECT_ROOT, "tmp"), exist_ok=True)
    with open(_PENDING_TG, "w", encoding="utf-8") as f:
        f.write(text)


def main():
    try:
        json.load(sys.stdin)
    except Exception:
        pass

    warnings = []

    # 1. pending_updates.json 잔여 항목
    pending = _load_pending()
    if pending:
        lines = ["⚠️  [DoD] 문서 갱신 미완료 항목:"]
        for src, info in pending.items():
            remaining = [d for d in info["required_docs"] if d not in info.get("cleared_docs", [])]
            if remaining:
                lines.append(f"  [{info['type'].upper()}] {src}  ({info['time']})")
                for d in remaining:
                    lines.append(f"    → {d}  미갱신")
        if len(lines) > 1:
            warnings.append("\n".join(lines))

    # 2. feature_map.md 존재 여부
    if not os.path.exists(_FEATURE_MAP):
        warnings.append(
            "⚠️  [DoD] docs/feature_map.md 없음\n"
            "    → '기능 매핑 문서 초기화해줘' 로 생성하세요\n"
            "    → 없으면 1개월 후 소스 전체를 다시 뒤져야 합니다"
        )

    # 3. 서비스 파일 테스트 누락
    warnings.extend(_check_service_tests())

    if not warnings:
        sys.stdout.buffer.write(b"[dod] All checks passed\n")
        # 클리어
        if os.path.exists(_PENDING_JSON):
            os.remove(_PENDING_JSON)
        return

    output = "\n[dod] ══ DoD 미완료 ══════════════════════════════════\n"
    output += "\n".join(warnings)
    output += "\n[dod] ═════════════════════════════════════════════════\n"
    sys.stdout.buffer.write(output.encode("utf-8"))
    _append_telegram(warnings)


if __name__ == "__main__":
    main()
