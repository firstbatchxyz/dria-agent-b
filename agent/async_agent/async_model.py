from openai import AsyncOpenAI
from pydantic import BaseModel

from typing import Optional, Union
import os
from dotenv import load_dotenv

from agent.settings import (
    OPENROUTER_API_KEY,
    OPENROUTER_BASE_URL,
    OPENROUTER_STRONG_MODEL,
    VLLM_HOST,
    VLLM_PORT,
)
from agent.schemas import ChatMessage, Role

# Load env for OPENAI usage (keeps behavior consistent with training/reward.py)
load_dotenv()

# Constants for OpenAI path (matching training/reward.py)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GPT_O3 = "o3-2025-04-16"


def create_async_openai_client() -> AsyncOpenAI:
    """Create a new AsyncOpenAI client instance."""
    return AsyncOpenAI(
        api_key=OPENROUTER_API_KEY,
        base_url=OPENROUTER_BASE_URL,
    )


def create_async_vllm_client(host: str = "0.0.0.0", port: int = 8000) -> AsyncOpenAI:
    """Create a new async vLLM client instance (OpenAI-compatible)."""
    return AsyncOpenAI(
        base_url=f"http://{host}:{port}/v1",
        api_key="EMPTY",  # vLLM doesn't require a real API key
    )


def create_async_openai_api_client() -> AsyncOpenAI:
    """Create a new AsyncOpenAI client instance for direct OpenAI API usage."""
    return AsyncOpenAI(api_key=OPENAI_API_KEY)


def _as_dict(msg: Union[ChatMessage, dict]) -> dict:
    """
    Accept either ChatMessage or raw dict and return the raw dict.

    Args:
        msg: A ChatMessage object or a raw dict.

    Returns:
        A raw dict.
    """
    return msg if isinstance(msg, dict) else msg.model_dump()


async def get_model_response(
    messages: Optional[list[ChatMessage]] = None,
    message: Optional[str] = None,
    system_prompt: Optional[str] = None,
    model: str = OPENROUTER_STRONG_MODEL,
    client: Optional[AsyncOpenAI] = None,
    use_vllm: bool = False,
    use_openai: bool = False,
) -> Union[str, BaseModel]:
    """
    Get a response from a model asynchronously using one of:
    - OpenAI Responses API with GPT-O3 (when use_opena=True)
    - OpenRouter (default)
    - vLLM (when use_vllm=True)

    Args:
        messages: A list of ChatMessage objects (optional).
        message: A single message string (optional).
        system_prompt: A system prompt for the model (optional).
        model: The model to use.
        client: Optional AsyncOpenAI client to use. If None, uses the global client.
        use_vllm: Whether to use vLLM backend instead of OpenRouter.
        use_opena: Whether to call the OpenAI API directly with GPT-O3.

    Returns:
        A string response from the model if schema is None, otherwise a BaseModel object.
    """
    if messages is None and message is None:
        raise ValueError("Either 'messages' or 'message' must be provided.")

    # Use provided clients or fall back to global ones
    if client is None or use_openai:
        # For use_opena=True, always use a fresh OpenAI client regardless of provided client
        if use_openai:
            client = create_async_openai_api_client()
        elif use_vllm:
            client = create_async_vllm_client(host=VLLM_HOST, port=VLLM_PORT)
        else:
            client = create_async_openai_client()

    # Build message history
    if messages is None:
        messages = []
        if system_prompt:
            messages.append(
                _as_dict(ChatMessage(role=Role.SYSTEM, content=system_prompt))
            )
        messages.append(_as_dict(ChatMessage(role=Role.USER, content=message)))
    else:
        messages = [_as_dict(m) for m in messages]

    if use_openai:
        # Use OpenAI Responses API with GPT-O3, mirroring training/reward.py
        completion = await client.responses.create(
            model=GPT_O3,
            input=messages,
        )
        return completion.output_text
    elif use_vllm:
        completion = await client.chat.completions.create(
            model=model, messages=messages
        )

        return completion.choices[0].message.content
    else:
        completion = await client.chat.completions.create(
            model=model, messages=messages
        )
        return completion.choices[0].message.content
