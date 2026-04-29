"""
Stop Hook — Synology Chat 알림 발송.

동작:
  1. tmp/telegram_pending.txt 존재 시 내용 발송 후 삭제
  2. 없으면 git diff 기반 자동 요약 발송

환경변수 (.env):
  SYNOLOGY_BASE_URL
  SYNOLOGY_BOT_TOKEN
  SYNOLOGY_BOT_USER_ID
"""

import json
import os
import sys
import urllib.parse
import urllib.request
import subprocess
from datetime import date

_HOOK_DIR     = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.abspath(os.path.join(_HOOK_DIR, "..", ".."))
_PENDING      = os.path.join(_PROJECT_ROOT, "tmp", "telegram_pending.txt")
_ENV_PATH     = os.path.join(_PROJECT_ROOT, ".env")


def _load_env():
    cfg = {}
    try:
        with open(_ENV_PATH, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                for key in ("SYNOLOGY_BASE_URL", "SYNOLOGY_BOT_TOKEN", "SYNOLOGY_BOT_USER_ID"):
                    if line.startswith(f"{key}="):
                        cfg[key] = line.split("=", 1)[1].strip()
    except FileNotFoundError:
        pass
    return cfg


def _send(cfg: dict, text: str) -> bool:
    token    = cfg.get("SYNOLOGY_BOT_TOKEN", "")
    base_url = cfg.get("SYNOLOGY_BASE_URL", "").rstrip("/")
    bot_uid  = int(cfg.get("SYNOLOGY_BOT_USER_ID", "0"))

    if not token or not base_url or not bot_uid:
        sys.stderr.buffer.write(b"[synology] 환경변수 미설정 — skipping\n")
        return False

    url      = f"{base_url}/webapi/entry.cgi?api=SYNO.Chat.External&version=2&method=chatbot&token={urllib.parse.quote(token)}"
    payload  = json.dumps({"text": text, "user_ids": [bot_uid]})
    data     = urllib.parse.urlencode({"payload": payload}).encode()
    req      = urllib.request.Request(url, data=data, method="POST")
    try:
        import ssl
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        with urllib.request.urlopen(req, timeout=10, context=ctx) as resp:
            result = json.loads(resp.read())
            return result.get("success", False)
    except Exception as e:
        sys.stderr.buffer.write(f"[synology] 오류: {e}\n".encode())
        return False


def _git_changed_files() -> list:
    files = []
    for cmd in [["git", "diff", "--name-only", "HEAD"],
                ["git", "diff", "--name-only", "--cached"]]:
        try:
            r = subprocess.run(cmd, cwd=_PROJECT_ROOT,
                               capture_output=True, text=True, timeout=5)
            files += [f.strip() for f in r.stdout.splitlines() if f.strip()]
        except Exception:
            pass
    return list(set(files))


def _build_auto_message(files: list) -> str:
    today    = date.today().isoformat()
    backend  = [f for f in files if f.endswith(".py")]
    frontend = [f for f in files if f.endswith((".html", ".js", ".ts", ".css"))]
    docs     = [f for f in files if f.endswith(".md")]
    lines    = ["[auto] 세션 종료 — 변경사항 요약", "=== 파일 변경 ==="]
    if backend:
        lines.append("[백엔드] " + ", ".join(backend[:5]))
    if frontend:
        lines.append("[프론트엔드] " + ", ".join(frontend[:5]))
    if docs:
        lines.append("[문서] " + ", ".join(docs[:3]))
    if not (backend or frontend or docs):
        return ""
    lines.append(f"작성일: {today} / 작성자: Claude (auto)")
    return "\n".join(lines)


def main():
    try:
        json.load(sys.stdin)
    except Exception:
        pass

    cfg = _load_env()

    # 1순위: Claude 가 직접 작성한 pending.txt
    if os.path.exists(_PENDING):
        with open(_PENDING, encoding="utf-8") as f:
            text = f.read().strip()
        if text:
            if _send(cfg, text):
                os.remove(_PENDING)
                sys.stdout.buffer.write(b"[synology] notification sent (pending)\n")
            else:
                sys.stderr.buffer.write(b"[synology] failed, pending file kept\n")
            return
        os.remove(_PENDING)

    # 2순위: git diff 자동 감지
    changed = _git_changed_files()
    if changed:
        text = _build_auto_message(changed)
        if text:
            if _send(cfg, text):
                sys.stdout.buffer.write(b"[synology] notification sent (auto)\n")


if __name__ == "__main__":
    main()
