"""
Stop Hook - Telegram notification on task completion.

개선사항 (v2):
  - git diff --name-only 로 변경 파일 자동 감지
  - telegram_pending.txt 없어도 변경사항 있으면 자동 요약 발송
  - pending.txt 있으면 우선 사용 (Claude가 직접 작성한 상세 메시지)
"""

import json
import os
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import date

_HOOK_DIR     = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.abspath(os.path.join(_HOOK_DIR, "..", ".."))
_PENDING      = os.path.join(_PROJECT_ROOT, "tmp", "telegram_pending.txt")
_ENV_PATH     = os.path.join(_PROJECT_ROOT, ".env")


def _load_env():
    token, chat_id = None, None
    try:
        with open(_ENV_PATH, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line.startswith("TELEGRAM_BOT_TOKEN="):
                    token = line.split("=", 1)[1].strip()
                elif line.startswith("TELEGRAM_CHAT_ID="):
                    chat_id = line.split("=", 1)[1].strip()
    except FileNotFoundError:
        pass
    return token, chat_id


def _git_changed_files() -> list[str]:
    """git diff --name-only HEAD 로 변경된 파일 목록 반환."""
    try:
        result = subprocess.run(
            ["git", "diff", "--name-only", "HEAD"],
            cwd=_PROJECT_ROOT,
            capture_output=True,
            text=True,
            timeout=5,
        )
        files = [f.strip() for f in result.stdout.splitlines() if f.strip()]
        # staged 파일도 포함
        result2 = subprocess.run(
            ["git", "diff", "--name-only", "--cached"],
            cwd=_PROJECT_ROOT,
            capture_output=True,
            text=True,
            timeout=5,
        )
        files += [f.strip() for f in result2.stdout.splitlines() if f.strip()]
        return list(set(files))
    except Exception:
        return []


def _build_auto_message(changed_files: list[str]) -> str:
    """변경 파일 기반 자동 요약 메시지 생성."""
    today = date.today().isoformat()
    backend  = [f for f in changed_files if f.endswith(".py")]
    frontend = [f for f in changed_files if f.endswith((".html", ".js", ".ts", ".css"))]
    docs     = [f for f in changed_files if f.endswith(".md")]

    lines = [
        "[auto] 세션 종료 — 변경사항 요약",
        "=== 파일 변경 ===",
    ]
    if backend:
        lines.append("[백엔드] " + ", ".join(backend[:5]))
    if frontend:
        lines.append("[프론트엔드] " + ", ".join(frontend[:5]))
    if docs:
        lines.append("[문서] " + ", ".join(docs[:3]))
    if not (backend or frontend or docs):
        return ""  # 의미있는 변경 없으면 발송 안 함

    lines.append(f"작성일: {today} / 작성자: Claude (auto)")
    return "\n".join(lines)


def _send(token: str, chat_id: str, text: str) -> bool:
    url  = f"https://api.telegram.org/bot{token}/sendMessage"
    data = urllib.parse.urlencode({"chat_id": chat_id, "text": text}).encode()
    req  = urllib.request.Request(url, data=data, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return resp.status == 200
    except urllib.error.URLError as e:
        sys.stderr.buffer.write(f"[telegram] send failed: {e}\n".encode("utf-8"))
        return False


def main():
    try:
        json.load(sys.stdin)
    except Exception:
        pass

    token, chat_id = _load_env()
    if not token or not chat_id:
        sys.stderr.buffer.write(b"[telegram] TOKEN or CHAT_ID not set — skipping\n")
        return

    # 1순위: Claude가 직접 작성한 pending.txt
    if os.path.exists(_PENDING):
        with open(_PENDING, encoding="utf-8") as f:
            text = f.read().strip()
        if text:
            if _send(token, chat_id, text):
                os.remove(_PENDING)
                sys.stdout.buffer.write(b"[telegram] notification sent (pending)\n")
            else:
                sys.stderr.buffer.write(b"[telegram] failed, pending file kept\n")
            return
        os.remove(_PENDING)

    # 2순위: git diff 기반 자동 감지
    changed = _git_changed_files()
    if changed:
        text = _build_auto_message(changed)
        if text:
            if _send(token, chat_id, text):
                sys.stdout.buffer.write(b"[telegram] notification sent (auto)\n")
            else:
                sys.stderr.buffer.write(b"[telegram] auto send failed\n")


if __name__ == "__main__":
    main()
