"""
Synology Chat MCP Server — 발송 전용 (단방향)

제공 도구:
  - send_message      : 채널/사용자에게 메시지 발송
  - get_channel_list  : 채널 목록 조회
  - get_user_list     : 사용자 목록 조회

환경변수 (.env):
  SYNOLOGY_BASE_URL  = https://devmon.synology.me:5001
  SYNOLOGY_BOT_TOKEN = your_token
"""

import asyncio
import json
import os

import httpx
import urllib.parse
from dotenv import load_dotenv
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool

load_dotenv()

BASE_URL  = os.getenv("SYNOLOGY_BASE_URL", "").rstrip("/")
BOT_TOKEN = os.getenv("SYNOLOGY_BOT_TOKEN", "")


# ── API 호출 ──────────────────────────────────────────────────

async def _call(method: str, payload: dict) -> dict:
    """Synology Chat Bot API 호출."""
    url = (
        f"{BASE_URL}/webapi/entry.cgi"
        f"?api=SYNO.Chat.External&version=2&method={method}"
        f"&token={urllib.parse.quote(BOT_TOKEN)}"
    )
    async with httpx.AsyncClient(verify=False, timeout=10) as client:
        resp = await client.post(url, data={"payload": json.dumps(payload)})
        resp.raise_for_status()
        return resp.json()


async def _get(method: str, params: dict = {}) -> dict:
    url = (
        f"{BASE_URL}/webapi/entry.cgi"
        f"?api=SYNO.Chat.External&version=2&method={method}"
        f"&token={urllib.parse.quote(BOT_TOKEN)}"
    )
    async with httpx.AsyncClient(verify=False, timeout=10) as client:
        resp = await client.get(url, params=params)
        resp.raise_for_status()
        return resp.json()


# ── 도구 정의 ─────────────────────────────────────────────────

TOOLS = [
    Tool(
        name="send_message",
        description=(
            "Synology Chat 채널 또는 사용자에게 메시지를 발송합니다. "
            "작업 완료 알림, DoD 경고, 배포 알림 등에 사용합니다."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "text": {
                    "type": "string",
                    "description": "발송할 메시지 텍스트",
                },
                "user_ids": {
                    "type": "array",
                    "items": {"type": "integer"},
                    "description": "수신자 user_id 목록 (user_ids 또는 channel_id 중 하나 필수)",
                },
                "channel_id": {
                    "type": "integer",
                    "description": "발송할 채널 ID (user_ids 또는 channel_id 중 하나 필수)",
                },
            },
            "required": ["text"],
        },
    ),
    Tool(
        name="get_channel_list",
        description="접근 가능한 Synology Chat 채널 목록과 ID 를 반환합니다.",
        inputSchema={"type": "object", "properties": {}},
    ),
    Tool(
        name="get_user_list",
        description="Synology Chat 사용자 목록과 ID 를 반환합니다.",
        inputSchema={"type": "object", "properties": {}},
    ),
]


# ── 도구 실행 ─────────────────────────────────────────────────

async def handle_tool(name: str, args: dict) -> list[TextContent]:
    if not BASE_URL or not BOT_TOKEN:
        return [TextContent(
            type="text",
            text="❌ SYNOLOGY_BASE_URL 또는 SYNOLOGY_BOT_TOKEN 이 설정되지 않았습니다.\n"
                 "   .env 파일을 확인하세요."
        )]

    try:
        if name == "send_message":
            payload = {"text": args["text"]}
            if "user_ids" in args:
                payload["user_ids"] = args["user_ids"]
            if "channel_id" in args:
                payload["channel_id"] = args["channel_id"]
            result = await _call("chatbot", payload)
            ok = result.get("success", False)
            return [TextContent(
                type="text",
                text="✅ 발송 완료" if ok else f"❌ 발송 실패: {result}"
            )]

        elif name == "get_channel_list":
            result = await _get("channel_list")
            channels = result.get("data", {}).get("channels", [])
            if not channels:
                return [TextContent(type="text", text="채널 없음 (Bot 이 초대된 채널만 표시됩니다)")]
            lines = [f"ID: {c['channel_id']}  이름: {c['name']}" for c in channels]
            return [TextContent(type="text", text="\n".join(lines))]

        elif name == "get_user_list":
            result = await _get("user_list")
            users = result.get("data", {}).get("users", [])
            if not users:
                return [TextContent(type="text", text="사용자 없음")]
            lines = [f"ID: {u['user_id']}  이름: {u['username']}" for u in users]
            return [TextContent(type="text", text="\n".join(lines))]

    except httpx.HTTPError as e:
        return [TextContent(type="text", text=f"❌ HTTP 오류: {e}")]
    except Exception as e:
        return [TextContent(type="text", text=f"❌ 오류: {e}")]


# ── MCP 서버 실행 ─────────────────────────────────────────────

async def run():
    server = Server("synology-chat-mcp")

    @server.list_tools()
    async def list_tools():
        return TOOLS

    @server.call_tool()
    async def call_tool(name: str, arguments: dict):
        return await handle_tool(name, arguments)

    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options()
        )


if __name__ == "__main__":
    asyncio.run(run())
