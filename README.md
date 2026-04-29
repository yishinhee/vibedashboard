# Claude Harness 설정 패키지
> DEVMON · 2026-04-28

---

## 패키지 구조

```
claude-harness-setup/
├── README.md                          # 이 파일
├── setup.sh                           # 자동 설정 스크립트
├── CLAUDE.md                          # 전역 고정 하네스 (수정 금지)
├── agents.template.md                 # 새 프로젝트용 템플릿
├── .env.global                        # 환경변수 참조본
├── .claude/
│   ├── hooks/
│   │   ├── sync_structure.py
│   │   ├── dod_check.py
│   │   ├── telegram_notify.py
│   │   └── synology_notify.py
│   └── skills/
│       ├── feature_map_update/SKILL.md
│       └── new_project_setup/SKILL.md
├── mcp/synology-chat-mcp/
│   ├── server.py
│   ├── requirements.txt
│   └── .env.example
├── global-claude-config/
│   └── claude_desktop_config.json
└── harness-dashboard/                 # 테스트 프로젝트
    ├── CLAUDE.md / agents.md / .env
    ├── docs/feature_map.md
    └── .claude/ (hooks + skills)
```

---

## 빠른 시작

### 자동 (권장)
```bash
bash setup.sh
```

### 수동
```
1. global-claude-config/claude_desktop_config.json
   -> C:\Users\shinh\.claude\claude_desktop_config.json

2. mcp/synology-chat-mcp/
   -> C:\Users\shinh\.claude\mcp\synology-chat-mcp\
   pip install -r requirements.txt

3. harness-dashboard/ 원하는 위치에 복사

4. Claude Code 재시작
```

---

## 설정된 값

| 항목 | 값 |
|---|---|
| Synology Chat URL | https://devmon.synology.me:5001 |
| Bot User ID | 8 |
| Channel ID | 438 |

> **주의**: 토큰이 포함되어 있습니다. 배포 전 반드시 재발급하세요.
> Synology Chat -> 통합 -> Bot -> CLAUDE -> 토큰 재발급

---

## 새 프로젝트 적용

```bash
cp CLAUDE.md ./새프로젝트/
cp agents.template.md ./새프로젝트/agents.md
mkdir -p .claude/hooks .claude/skills/feature_map_update tmp
cp .claude/hooks/* ./새프로젝트/.claude/hooks/
# agents.md 수정 후 시작
```
