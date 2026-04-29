#!/bin/bash
# =============================================================
# Claude Harness 전체 설정 자동화 스크립트
# 사용법: bash setup.sh
# =============================================================

set -e

BLUE='\033[0;34m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

log()  { echo -e "${BLUE}[setup]${NC} $1"; }
ok()   { echo -e "${GREEN}[ok]${NC}    $1"; }
warn() { echo -e "${YELLOW}[warn]${NC}  $1"; }
err()  { echo -e "${RED}[error]${NC} $1"; exit 1; }

echo ""
echo "=================================================="
echo "  Claude Harness 설정 자동화"
echo "  DEVMON Internal Setup Script"
echo "=================================================="
echo ""

# ── OS 감지 ──────────────────────────────────────────────────
detect_os() {
    if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "cygwin" || "$OSTYPE" == "win32" ]]; then
        echo "windows"
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        echo "mac"
    else
        echo "linux"
    fi
}
OS=$(detect_os)
log "OS 감지: $OS"

# ── 전역 .claude 경로 ─────────────────────────────────────────
if [[ "$OS" == "windows" ]]; then
    CLAUDE_HOME="$USERPROFILE/.claude"
    CLAUDE_HOME_DISPLAY='%USERPROFILE%\.claude'
elif [[ "$OS" == "mac" ]]; then
    CLAUDE_HOME="$HOME/Library/Application Support/Claude"
else
    CLAUDE_HOME="$HOME/.claude"
fi
log "전역 .claude 경로: $CLAUDE_HOME"

# ── Step 1: 전역 .claude 설정 ─────────────────────────────────
log "Step 1/4  전역 Claude 설정 배치..."

mkdir -p "$CLAUDE_HOME/mcp/synology-chat-mcp"

# claude_desktop_config.json
if [[ -f "$CLAUDE_HOME/claude_desktop_config.json" ]]; then
    warn "claude_desktop_config.json 이미 존재 — 백업 후 덮어씀"
    cp "$CLAUDE_HOME/claude_desktop_config.json" \
       "$CLAUDE_HOME/claude_desktop_config.json.bak.$(date +%Y%m%d%H%M%S)"
fi
cp global-claude-config/claude_desktop_config.json "$CLAUDE_HOME/claude_desktop_config.json"
ok "claude_desktop_config.json 배치 완료"

# MCP 서버 파일
cp mcp/synology-chat-mcp/server.py       "$CLAUDE_HOME/mcp/synology-chat-mcp/"
cp mcp/synology-chat-mcp/requirements.txt "$CLAUDE_HOME/mcp/synology-chat-mcp/"
ok "Synology Chat MCP 파일 배치 완료"

# MCP .env
MCP_ENV="$CLAUDE_HOME/mcp/synology-chat-mcp/.env"
if [[ ! -f "$MCP_ENV" ]]; then
    cp mcp/synology-chat-mcp/.env.example "$MCP_ENV"
    ok "MCP .env 생성 완료"
else
    warn "MCP .env 이미 존재 — 건너뜀"
fi

# ── Step 2: MCP 패키지 설치 ───────────────────────────────────
log "Step 2/4  MCP 패키지 설치..."
if command -v pip &> /dev/null; then
    pip install -r "$CLAUDE_HOME/mcp/synology-chat-mcp/requirements.txt" -q
    ok "MCP 패키지 설치 완료"
else
    warn "pip 없음 — 수동 설치 필요: pip install -r requirements.txt"
fi

# ── Step 3: harness-dashboard 프로젝트 설정 ───────────────────
log "Step 3/4  harness-dashboard 프로젝트 설정..."

PROJECT="harness-dashboard"
if [[ ! -d "$PROJECT" ]]; then
    warn "harness-dashboard 디렉토리 없음 — 현재 위치에 생성"
fi

# 디렉토리 구조 보장
mkdir -p "$PROJECT/.claude/hooks"
mkdir -p "$PROJECT/.claude/skills/feature_map_update"
mkdir -p "$PROJECT/docs"
mkdir -p "$PROJECT/tmp"
ok "디렉토리 구조 생성 완료"

# 파일 복사 (이미 있으면 유지)
[[ ! -f "$PROJECT/CLAUDE.md" ]]  && cp CLAUDE.md "$PROJECT/CLAUDE.md" && ok "CLAUDE.md 복사"
[[ ! -f "$PROJECT/agents.md" ]]  && cp harness-dashboard/agents.md "$PROJECT/agents.md" && ok "agents.md 복사"
[[ ! -f "$PROJECT/.gitignore" ]] && cp harness-dashboard/.gitignore "$PROJECT/.gitignore" && ok ".gitignore 복사"
[[ ! -f "$PROJECT/docs/feature_map.md" ]] && cp harness-dashboard/docs/feature_map.md "$PROJECT/docs/" && ok "feature_map.md 복사"

# hooks 복사
for hook in sync_structure.py dod_check.py telegram_notify.py synology_notify.py; do
    cp ".claude/hooks/$hook" "$PROJECT/.claude/hooks/$hook"
done
ok "hooks 4개 복사 완료"

# skills 복사
cp ".claude/skills/feature_map_update/SKILL.md" \
   "$PROJECT/.claude/skills/feature_map_update/SKILL.md"
ok "skills 복사 완료"

# .env
if [[ ! -f "$PROJECT/.env" ]]; then
    cp harness-dashboard/.env "$PROJECT/.env"
    ok ".env 생성 완료"
else
    warn ".env 이미 존재 — 건너뜀 (토큰 확인 필요)"
fi

# 프로젝트 .claude/claude_desktop_config.json
cp harness-dashboard/.claude/claude_desktop_config.json \
   "$PROJECT/.claude/claude_desktop_config.json"
ok "프로젝트 claude_desktop_config.json 복사 완료"

# ── Step 4: 완료 안내 ─────────────────────────────────────────
log "Step 4/4  설정 완료"

echo ""
echo "=================================================="
echo -e "  ${GREEN}설정 완료${NC}"
echo "=================================================="
echo ""
echo "다음 할 일:"
echo ""
echo "  1. 토큰 재발급 (대화 중 노출됨)"
echo "     Synology Chat -> 통합 -> Bot -> CLAUDE -> 토큰 재발급"
echo "     아래 파일들의 토큰값 업데이트:"
echo "     - $CLAUDE_HOME/claude_desktop_config.json"
echo "     - $CLAUDE_HOME/mcp/synology-chat-mcp/.env"
echo "     - $PROJECT/.env"
echo ""
echo "  2. harness-dashboard Django 초기화"
echo "     cd $PROJECT"
echo "     python -m venv venv"
if [[ "$OS" == "windows" ]]; then
echo "     venv\\Scripts\\activate"
else
echo "     source venv/bin/activate"
fi
echo "     pip install django==5.0 python-dotenv httpx"
echo ""
echo "  3. Claude Code 재시작 (MCP 로드)"
echo ""
echo "  4. Claude Code 에서 테스트:"
echo "     '채널 목록 보여줘' -> Synology Chat MCP 동작 확인"
echo ""
echo -e "  ${YELLOW}주의: .env 파일은 git commit 하지 마세요${NC}"
echo ""
