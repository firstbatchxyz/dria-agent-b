# save as quick_check.py (repo root)
import asyncio
from fastmcp import Client

# Point client at the Python file; FastMCP will run it via stdio
client = Client("mcp_server/server.py")  # change path if needed

async def main():
    async with client:
        tools = await client.list_tools()
        print("TOOLS:", [t.name for t in tools])
        result = await client.call_tool("use_memory_agent", {"question": "I'm happy that today is my birthday"})
        print(result)

asyncio.run(main())