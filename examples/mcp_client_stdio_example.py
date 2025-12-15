"""
Simple MCP stdio client example

This non-interactive example connects to the stdio MCP server, lists tools,
runs a `scan_directory` against the current directory, and prints the result.

Run:

python -m examples.mcp_client_stdio_example

Note: Ensure dependencies are installed (see pyproject.toml) and Python >=3.13.
"""

import asyncio
import json
from contextlib import AsyncExitStack
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def main():
    server_params = StdioServerParameters(
        command="python",
        args=["-m", "src.mcp_server.server"],
    )

    async with AsyncExitStack() as stack:
        stdio_transport = await stack.enter_async_context(stdio_client(server_params))
        stdio, write = stdio_transport

        session = await stack.enter_async_context(ClientSession(stdio, write))
        await session.initialize()

        # List tools
        tools_response = await session.list_tools()
        tools = tools_response.tools
        print(f"Found {len(tools)} tools:\n")
        for t in tools:
            print(f"- {t.name}: {t.description}")

        # Call a simple fast tool: scan_directory on a GitHub repo
        print("\nCalling scan_directory on 'https://github.com/duongle-wizeline/wizelit'...")
        try:
            result = await session.call_tool("scan_directory", arguments={
                "root_directory": "https://github.com/duongle-wizeline/wizelit",
                "pattern": "*.py",
            })

            # The server returns TextContent with natural language or JSON text
            text = result.content[0].text
            try:
                parsed = json.loads(text)
                print(json.dumps(parsed, indent=2))
            except json.JSONDecodeError:
                print(text)

        except Exception as e:
            print(f"Error calling tool: {e}")

        # --- Additional example cases for finding symbol `create_chat_settings` ---
        async def call_and_print(tool_name, arguments, description=None):
            if description:
                print(f"\n-- {description} --")
            try:
                resp = await session.call_tool(tool_name, arguments=arguments)
                text = resp.content[0].text
                try:
                    parsed = json.loads(text)
                    print(json.dumps(parsed, indent=2))
                except json.JSONDecodeError:
                    print(text)
            except Exception as e:
                print(f"Error calling {tool_name}: {e}")

        # 1) Find usages on the remote GitHub repo (direct URL)
        await call_and_print(
            "find_symbol",
            {"root_directory": "https://github.com/duongle-wizeline/wizelit", "symbol_name": "create_chat_settings"},
            description="Find usages (GitHub URL)"
        )

        # 2) Grep search for exact symbol (fast, no full scan needed)
        await call_and_print(
            "grep_search",
            {"root_directory": "https://github.com/duongle-wizeline/wizelit", "pattern": "create_chat_settings", "file_pattern": "*.py"},
            description="Grep search for 'create_chat_settings' (GitHub URL)"
        )

        # 3) Find usages assuming repo is cloned locally (faster)
        await call_and_print(
            "find_symbol",
            {"root_directory": ".", "symbol_name": "create_chat_settings"},
            description="Find usages (local path '.')"
        )


if __name__ == "__main__":
    asyncio.run(main())
