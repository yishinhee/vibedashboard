"""
Telegram + Synology Chat 동시 발송 wrapper.

문제:
  기존 .claude/hooks/telegram_notify.py / synology_notify.py 는 각자 발송 성공 시
  tmp/telegram_pending.txt 를 삭제 → 두 hook 동시 등록 시 한쪽만 발송됨.

해결:
  본 wrapper 가 두 채널 모두 발송을 시도한 뒤 한 번만 파일 삭제.

사용처:
  1) .claude/settings.json 의 Stop hook command:  python scripts/notify_all.py
  2) Claude 가 단계 완료 시점에 직접 호출 (agents.md §단계 완료 시 알림).

발송 정책:
  - tmp/telegram_pending.txt 가 있으면 그 내용을 우선 발송.
  - 없으면 git diff --name-only 로 변경 파일 자동 요약 발송.
  - Telegram / Synology 환경변수 미설정 채널은 skip (다른 채널은 시도).
  - 한쪽이라도 성공하면 pending 파일 삭제. 둘 다 실패하면 파일 유지.

stdin: Stop hook payload(JSON). 파싱 실패 무시.
"""
from __future__ import annotations

import json
import os
import ssl
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import date

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.abspath(os.path.join(_SCRIPT_DIR, ".."))
_PENDING = os.path.join(_PROJECT_ROOT, "tmp", "telegram_pending.txt")
_ENV_PATH = os.path.join(_PROJECT_ROOT, ".env")


def _load_env() -> dict[str, str]:
    cfg: dict[str, str] = {}
    if not os.path.exists(_ENV_PATH):
        return cfg
    with open(_ENV_PATH, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            cfg[k.strip()] = v.strip()
    return cfg


def _git_changed_files() -> list[str]:
    files: list[str] = []
    for cmd in (
        ["git", "diff", "--name-only", "HEAD"],
        ["git", "diff", "--name-only", "--cached"],
    ):
        try:
            r = subprocess.run(
                cmd, cwd=_PROJECT_ROOT,
                capture_output=True, text=True, timeout=5,
            )
            files += [f.strip() for f in r.stdout.splitlines() if f.strip()]
        except Exception:
            pass
    return list(set(files))


def _build_auto_message(changed: list[str]) -> str:
    today = date.today().isoformat()
    backend = [f for f in changed if f.endswith(".py")]
    frontend = [f for f in changed if f.endswith((".html", ".js", ".ts", ".css"))]
    docs = [f for f in changed if f.endswith(".md")]
    lines = ["[auto] 세션 종료 — 변경사항 요약", "=== 파일 변경 ==="]
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


def _send_telegram(cfg: dict[str, str], text: str) -> bool:
    token = cfg.get("TELEGRAM_BOT_TOKEN", "")
    chat_id = cfg.get("TELEGRAM_CHAT_ID", "")
    if not token or not chat_id:
        sys.stderr.buffer.write(b"[telegram] env not set, skip\n")
        return False
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    data = urllib.parse.urlencode({"chat_id": chat_id, "text": text}).encode()
    req = urllib.request.Request(url, data=data, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            ok = resp.status == 200
            sys.stdout.buffer.write(
                b"[telegram] sent\n" if ok else b"[telegram] non-200\n"
            )
            return ok
    except urllib.error.URLError as e:
        sys.stderr.buffer.write(f"[telegram] error: {e}\n".encode("utf-8"))
        return False


def _send_synology(cfg: dict[str, str], text: str) -> bool:
    base_url = cfg.get("SYNOLOGY_BASE_URL", "").rstrip("/")
    token = cfg.get("SYNOLOGY_BOT_TOKEN", "")
    bot_uid_str = cfg.get("SYNOLOGY_BOT_USER_ID", "0")
    if not (base_url and token and bot_uid_str):
        sys.stderr.buffer.write(b"[synology] env not set, skip\n")
        return False
    try:
        bot_uid = int(bot_uid_str)
    except ValueError:
        sys.stderr.buffer.write(b"[synology] invalid SYNOLOGY_BOT_USER_ID\n")
        return False

    url = (
        f"{base_url}/webapi/entry.cgi?api=SYNO.Chat.External"
        f"&version=2&method=chatbot&token={urllib.parse.quote(token)}"
    )
    payload = json.dumps({"text": text, "user_ids": [bot_uid]})
    data = urllib.parse.urlencode({"payload": payload}).encode()
    req = urllib.request.Request(url, data=data, method="POST")

    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    try:
        with urllib.request.urlopen(req, timeout=10, context=ctx) as resp:
            result = json.loads(resp.read())
            ok = bool(result.get("success"))
            sys.stdout.buffer.write(
                b"[synology] sent\n" if ok
                else f"[synology] non-success: {result}\n".encode("utf-8")
            )
            return ok
    except Exception as e:
        sys.stderr.buffer.write(f"[synology] error: {e}\n".encode("utf-8"))
        return False


def _resolve_message() -> str:
    if os.path.exists(_PENDING):
        with open(_PENDING, encoding="utf-8") as f:
            text = f.read().strip()
        if text:
            return text
    changed = _git_changed_files()
    return _build_auto_message(changed) if changed else ""


def main() -> None:
    try:
        json.load(sys.stdin)
    except Exception:
        pass

    text = _resolve_message()
    if not text:
        sys.stdout.buffer.write(b"[notify_all] nothing to send\n")
        return

    cfg = _load_env()
    sent_telegram = _send_telegram(cfg, text)
    sent_synology = _send_synology(cfg, text)

    if (sent_telegram or sent_synology) and os.path.exists(_PENDING):
        os.remove(_PENDING)
        sys.stdout.buffer.write(b"[notify_all] pending cleared\n")


if __name__ == "__main__":
    main()
