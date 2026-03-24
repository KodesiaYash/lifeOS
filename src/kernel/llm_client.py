"""
LLM provider abstraction via LiteLLM.
Provides completion, structured output, and embedding calls.
"""
from typing import Any

import structlog

from src.config import settings

logger = structlog.get_logger()


class LLMClient:
    """
    Unified LLM client wrapping LiteLLM for provider-agnostic calls.
    Supports: chat completion, structured output, streaming.
    """

    def __init__(
        self,
        model: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> None:
        self.model = model or settings.DEFAULT_LLM_MODEL
        self.temperature = temperature
        self.max_tokens = max_tokens

    async def complete(
        self,
        messages: list[dict[str, str]],
        model: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        **kwargs: Any,
    ) -> str:
        """
        Generate a chat completion.
        Returns the assistant's response text.
        """
        import litellm

        response = await litellm.acompletion(
            model=model or self.model,
            messages=messages,
            temperature=temperature if temperature is not None else self.temperature,
            max_tokens=max_tokens or self.max_tokens,
            **kwargs,
        )

        content = response.choices[0].message.content or ""
        logger.debug(
            "llm_completion",
            model=model or self.model,
            input_tokens=response.usage.prompt_tokens if response.usage else 0,
            output_tokens=response.usage.completion_tokens if response.usage else 0,
        )
        return content

    async def structured_output(
        self,
        messages: list[dict[str, str]],
        response_model: type,
        model: str | None = None,
        temperature: float | None = None,
        max_retries: int = 2,
    ) -> Any:
        """
        Generate a structured output parsed into a Pydantic model.
        Uses the instructor library for reliable structured extraction.
        """
        import instructor
        import openai

        client = instructor.from_openai(
            openai.AsyncOpenAI(api_key=settings.OPENAI_API_KEY),
        )

        result = await client.chat.completions.create(
            model=model or self.model,
            messages=messages,
            response_model=response_model,
            temperature=temperature if temperature is not None else self.temperature,
            max_retries=max_retries,
        )

        logger.debug(
            "llm_structured_output",
            model=model or self.model,
            response_model=response_model.__name__,
        )
        return result

    async def complete_with_tools(
        self,
        messages: list[dict[str, str]],
        tools: list[dict],
        model: str | None = None,
        temperature: float | None = None,
        **kwargs: Any,
    ) -> dict:
        """
        Generate a completion with tool/function calling.
        Returns the full response including any tool_calls.
        """
        import litellm

        response = await litellm.acompletion(
            model=model or self.model,
            messages=messages,
            tools=tools,
            temperature=temperature if temperature is not None else self.temperature,
            **kwargs,
        )

        message = response.choices[0].message
        logger.debug(
            "llm_tool_completion",
            model=model or self.model,
            tool_calls=len(message.tool_calls) if message.tool_calls else 0,
        )
        return {
            "content": message.content,
            "tool_calls": [
                {
                    "id": tc.id,
                    "function": {
                        "name": tc.function.name,
                        "arguments": tc.function.arguments,
                    },
                }
                for tc in (message.tool_calls or [])
            ],
            "usage": {
                "prompt_tokens": response.usage.prompt_tokens if response.usage else 0,
                "completion_tokens": response.usage.completion_tokens if response.usage else 0,
            },
        }
