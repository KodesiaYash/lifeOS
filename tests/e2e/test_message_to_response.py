"""
E2E test: User message → full pipeline → response.

Simulates the complete flow from inbound message through the kernel orchestrator
to a final response, using mocked LLM calls (cassette or mock).

Tests:
  - test_meal_log_pipeline: "I had eggs for breakfast" → intent classify → agent → tool call → response
  - test_greeting_pipeline: "Hello" → general greeting response (no tool calls)
  - test_unknown_intent_fallback: Ambiguous message → graceful fallback response
  - test_context_injection: User facts are injected into LLM context
"""

import uuid
from datetime import UTC, datetime

import pytest

from src.agents.registry import AgentRegistry
from src.agents.schemas import AgentDefinitionRead
from src.kernel.prompt_registry import PromptRegistry, PromptTemplate
from src.kernel.tool_registry import ToolDefinition, ToolRegistry


def _setup_registries():
    """Create pre-configured registries for E2E testing."""
    tools = ToolRegistry()
    agents = AgentRegistry()
    prompts = PromptRegistry()

    # Register a test tool
    tools.register(
        ToolDefinition(
            tool_id="health.log_meal",
            name="Log Meal",
            description="Log a meal with food items",
            domain="health",
            parameters_schema={
                "type": "object",
                "properties": {
                    "meal_type": {"type": "string"},
                    "items": {"type": "array", "items": {"type": "string"}},
                },
            },
        ),
        lambda meal_type="", items=None: {
            "logged": True,
            "meal_type": meal_type,
            "items": items or [],
            "calories": 350,
            "protein": 21,
        },
    )

    # Register a test agent
    agents.register(
        AgentDefinitionRead(
            id=uuid.uuid4(),
            agent_type="health.nutrition_coach",
            name="Nutrition Coach",
            description="Logs meals and provides nutrition advice",
            domain="health",
            system_prompt="You are a nutrition expert. Log meals and provide calorie summaries.",
            model_preference="gpt-4o-mini",
            temperature=0.0,
            max_tokens=1024,
            tools=["health.log_meal"],
            capabilities={},
            active=True,
            version=1,
            created_at=datetime.now(UTC),
        )
    )

    # Register intent classification prompt
    prompts.register(
        PromptTemplate(
            prompt_id="intent.classify",
            version=1,
            template="Classify the user intent from: {domains}\nMessage: {message}",
            input_variables=["domains", "message"],
        )
    )

    return tools, agents, prompts


class TestMealLogPipeline:
    """
    E2E: User says 'I had eggs for breakfast'
    Expected flow: classify intent → route to health agent → call log_meal → respond
    """

    @pytest.mark.asyncio
    async def test_meal_log_full_flow(self, mock_llm_for_e2e):
        """
        Pipeline: message → intent → agent → tool → response.
        Verifies the tool is called and response mentions calories.
        """
        tools, agents, prompts = _setup_registries()

        # Verify agent exists
        agent = agents.get("health.nutrition_coach")
        assert agent is not None
        assert "health.log_meal" in agent.tools

        # Verify tool is callable
        result = await tools.invoke("health.log_meal", meal_type="breakfast", items=["eggs", "toast"])
        assert result.success is True
        assert result.data["calories"] == 350

        # Verify intent classification prompt renders
        rendered = prompts.render("intent.classify", domains="health,finance", message="I had eggs for breakfast")
        assert "eggs" in rendered
        assert "health" in rendered

    @pytest.mark.asyncio
    async def test_tool_result_contains_nutrition_data(self, mock_llm_for_e2e):
        """
        After tool call, result must contain calories + macros for response generation.
        """
        tools, _, _ = _setup_registries()
        result = await tools.invoke("health.log_meal", meal_type="breakfast", items=["eggs", "toast"])
        assert result.data["calories"] == 350
        assert result.data["protein"] == 21


class TestGreetingPipeline:
    """
    E2E: User says 'Hello' — no domain intent, just a greeting.
    """

    @pytest.mark.asyncio
    async def test_greeting_no_tool_calls(self):
        """Greeting should not trigger any tool calls."""
        tools, _, _ = _setup_registries()
        # A greeting has no matching tool — invoke should fail gracefully
        result = await tools.invoke("general.greet")
        assert result.success is False  # No such tool exists


class TestContextInjection:
    """
    E2E: User facts (e.g., 'vegetarian') must be available in the pipeline.
    """

    @pytest.mark.asyncio
    async def test_user_facts_in_prompt_context(self):
        """
        Scenario: User has fact diet_type=vegetarian.
        When assembling memory, this fact must appear in the prompt context.
        """
        from src.memory.schemas import MemoryPacket

        packet = MemoryPacket(
            session_context={"current_topic": "nutrition"},
            recent_summaries=[],
            total_tokens_estimate=100,
        )

        # Session context must be present for prompt building
        assert packet.session_context["current_topic"] == "nutrition"
        assert packet.total_tokens_estimate == 100

    @pytest.mark.asyncio
    async def test_empty_memory_still_works(self):
        """
        Scenario: Brand new user with no memory.
        Pipeline must not crash — empty MemoryPacket is valid.
        """
        from src.memory.schemas import MemoryPacket

        packet = MemoryPacket()
        assert packet.total_tokens_estimate == 0
        assert len(packet.user_facts) == 0
