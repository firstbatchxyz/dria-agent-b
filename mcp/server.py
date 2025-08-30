import os
from typing import Optional

from fastmcp import FastMCP, Context

from agent import Agent
from mcp.settings import MEMORY_AGENT_NAME


mcp = FastMCP("Memory Agent Server")

# Initialize the agent
agent = Agent(
    model=MEMORY_AGENT_NAME,
    use_vllm=True,
    predetermined_memory_path=True,
    memory_path="mcp-server",
)

@mcp.tool
async def use_memory_agent(question: str) -> str:
    """
    Provide the local memory agent with the user query 
    so that it can (or not) interact with the memory and 
    return the response from the agent.

    Args:
        question: The user query to be processed by the agent.

    Returns:
        The response from the agent.
    """
    try:
        result = agent.chat(question)
        return result.reply or ""
    except Exception as exc:  
        return f"agent_error: {type(exc).__name__}: {exc}"


if __name__ == "__main__":
    host = "127.0.0.1"
    port = "8765"
    mcp.run(transport="http", host=host, port=port, path="/mcp-memory-agent")


