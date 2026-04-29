# Synology Chat MCP

Synology Chat Bot API 를 Claude 가 직접 사용할 수 있게 하는 MCP 서버.

## 제공 도구

| 도구 | 설명 |
|---|---|
| `send_message` | 채널 또는 사용자에게 메시지 발송 |
| `send_file_message` | 파일 링크 포함 메시지 발송 |
| `get_channel_list` | 채널 목록 조회 |
| `get_user_list` | 사용자 목록 조회 |
| `receive_messages` | Bot 으로 수신된 메시지 읽기 |

---

## 설치

```bash
cd mcp/synology-chat-mcp
pip install -r requirements.txt
cp .env.example .env
# .env 에 실제 값 입력
```

---

## Synology Chat 설정

### 1. Bot 생성
```
Synology Chat → 우측 상단 메뉴 → 통합 → Bot
→ "+ 생성" 클릭
→ Bot 이름 입력
→ Outgoing Webhook URL 입력:
   http://[이-서버-IP]:[WEBHOOK_PORT]/webhook
   예: http://192.168.1.100:8765/webhook
→ 생성 후 토큰 복사 → .env 의 SYNOLOGY_BOT_TOKEN 에 입력
```

### 2. 포트 확인
```
WEBHOOK_PORT (기본 8765) 가 방화벽에서 허용돼 있어야 함
NAS → 외부 접근이면 공유기 포트포워딩 필요
```

---

## claude_desktop_config.json 등록

```json
"mcpServers": {
  "synology-chat": {
    "command": "python",
    "args": ["/절대경로/.claude/mcp/synology-chat-mcp/server.py"],
    "env": {
      "SYNOLOGY_BASE_URL": "https://your-nas-ip:5001",
      "SYNOLOGY_BOT_TOKEN": "your_bot_token",
      "WEBHOOK_PORT": "8765"
    }
  }
}
```

---

## 사용 예시

### Claude 에게 직접 지시
```
"Synology Chat 의 개발팀 채널에 배포 완료 메시지 보내줘"
"Bot 으로 받은 메시지 확인해줘"
"user_id 5 인 사람한테 작업 완료 알림 보내줘"
```

### telegram_notify.py 대체
현재 `telegram_notify.py` 의 Stop Hook 역할을 이 MCP 로 대체 가능.
`dod_check.py` 에서 경고 발생 시 Claude 가 자동으로 `send_message` 도구 호출.

---

## 주의사항

- Synology Chat Bot API 는 NAS 펌웨어 버전에 따라 엔드포인트가 다를 수 있음
- DSM 7.x 기준으로 작성됨
- NAS 의 자체 서명 인증서 사용 시 `verify=False` 로 설정돼 있음 (운영 환경에서는 인증서 적용 권장)
- Outgoing Webhook 수신 서버(FastAPI)는 MCP 서버 내부에서 별도 스레드로 실행됨
