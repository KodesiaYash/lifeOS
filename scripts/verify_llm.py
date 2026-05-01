#!/usr/bin/env python3
"""
Verify LLM connectivity with minimal token usage.
Tests each configured provider with a simple "Hi" prompt.

Usage:
    python -m scripts.verify_llm

Environment variables required (at least one):
    OPENAI_API_KEY, ANTHROPIC_API_KEY, GEMINI_API_KEY, GROQ_API_KEY, MISTRAL_API_KEY
"""

import asyncio
import os
import sys

# Minimal test - just check if we can get a response
TEST_PROMPT = "Hi"
MAX_TOKENS = 5  # Absolute minimum


async def test_provider(provider: str, model: str, api_key_env: str) -> tuple[str, bool, str]:
    """Test a single LLM provider. Returns (provider, success, message)."""
    api_key = os.getenv(api_key_env)
    if not api_key:
        return (provider, False, f"No {api_key_env} set")

    try:
        import litellm

        response = await litellm.acompletion(
            model=model,
            messages=[{"role": "user", "content": TEST_PROMPT}],
            max_tokens=MAX_TOKENS,
            api_key=api_key,
        )
        content = response.choices[0].message.content
        return (provider, True, f"OK - got response: {content[:20]}...")
    except Exception as e:
        return (provider, False, f"Error: {str(e)[:50]}")


async def main() -> int:
    """Test all configured LLM providers."""
    providers = [
        ("OpenAI", "gpt-4o-mini", "OPENAI_API_KEY"),
        ("Anthropic", "claude-3-haiku-20240307", "ANTHROPIC_API_KEY"),
        ("Gemini", "gemini/gemini-1.5-flash", "GEMINI_API_KEY"),
        ("Groq", "groq/llama3-8b-8192", "GROQ_API_KEY"),
        ("Mistral", "mistral/mistral-small-latest", "MISTRAL_API_KEY"),
    ]

    print("🔍 Testing LLM Provider Connectivity")
    print("=" * 50)

    # Filter to only providers with API keys set
    configured = [(p, m, k) for p, m, k in providers if os.getenv(k)]

    if not configured:
        print("❌ No LLM API keys configured!")
        print("   Set at least one of: OPENAI_API_KEY, ANTHROPIC_API_KEY, etc.")
        return 1

    # Test all configured providers concurrently
    tasks = [test_provider(p, m, k) for p, m, k in configured]
    results = await asyncio.gather(*tasks)

    # Print results
    all_passed = True
    for provider, success, message in results:
        status = "✅" if success else "❌"
        print(f"{status} {provider}: {message}")
        if not success:
            all_passed = False

    print("=" * 50)
    if all_passed:
        print(f"✅ All {len(results)} configured providers working!")
        return 0
    else:
        failed = sum(1 for _, s, _ in results if not s)
        print(f"❌ {failed}/{len(results)} providers failed")
        return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
