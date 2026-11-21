# /// script
# requires-python = ">=3.12"
# dependencies = ["mcp>=1.2,<2"]
# ///
"""Check the Blender Lab MCP end to end: run code, take a window screenshot,
search the API docs. Needs a Blender with the MCP bridge listening
(`just blender-agent`). Prints one "BLENDER-MCP ok ..." line on success.

Run: uv run tools/setup/checks/blender_mcp_check.py <blender_mcp checkout>/mcp
"""

import asyncio
import json
import os
import sys

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.types import ImageContent, TextContent


def text_of(result: object) -> str:
    """Join the text parts of a tool result."""
    return "".join(
        c.text for c in getattr(result, "content", []) if isinstance(c, TextContent)
    )


async def check(mcp_dir: str) -> str:
    params = StdioServerParameters(
        command="uv",
        args=["--directory", mcp_dir, "run", "--quiet", "blender-mcp"],
        env=dict(os.environ),
    )
    async with (
        stdio_client(params) as (read, write),
        ClientSession(read, write) as session,
    ):
        await session.initialize()
        code = await session.call_tool(
            "execute_blender_code",
            {"code": "import bpy\nresult = {'version': bpy.app.version_string}"},
        )
        version = json.loads(text_of(code)).get("result", {}).get("version", "")
        if not version.startswith("5.2"):
            raise SystemExit(
                f"execute_blender_code: unexpected reply {text_of(code)[:300]}"
            )
        shot = await session.call_tool("get_screenshot_of_window_as_image", {})
        if not any(isinstance(c, ImageContent) for c in shot.content):
            raise SystemExit(f"screenshot: no image in reply {text_of(shot)[:300]}")
        docs = await session.call_tool(
            "search_api_docs", {"query": "export_scene gltf", "max_results": 3}
        )
        if "bpy.ops.export_scene" not in text_of(docs):
            raise SystemExit("search_api_docs: no glTF export entry found")
        return version


if __name__ == "__main__":
    print(f"BLENDER-MCP ok blender={asyncio.run(check(sys.argv[1]))}")
