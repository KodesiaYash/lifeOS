"""
Health & Fitness domain plugin.
Tracks nutrition, exercise, sleep, vitals, and wellness metrics.
"""

from src.domains.plugin import (
    AgentDeclaration,
    DomainPlugin,
    EventHandlerDeclaration,
    MemoryCategoryDeclaration,
    ToolDeclaration,
)

DOMAIN_ID = "health"
DOMAIN_NAME = "Health & Fitness"
DOMAIN_VERSION = "0.1.0"


# ---------------------------------------------------------------------------
# Stub tool handlers (replaced with real implementations in Phase 1)
# ---------------------------------------------------------------------------
async def _log_meal(**kwargs):
    """Stub: Log a meal. Phase 1 will parse NLP, estimate calories, persist."""
    return {"status": "stub", "action": "log_meal", "input": kwargs}


async def _log_exercise(**kwargs):
    """Stub: Log an exercise session."""
    return {"status": "stub", "action": "log_exercise", "input": kwargs}


async def _log_sleep(**kwargs):
    """Stub: Log sleep data."""
    return {"status": "stub", "action": "log_sleep", "input": kwargs}


async def _get_nutrition_summary(**kwargs):
    """Stub: Return daily/weekly nutrition summary."""
    return {"status": "stub", "action": "get_nutrition_summary", "input": kwargs}


async def _get_exercise_summary(**kwargs):
    """Stub: Return exercise summary."""
    return {"status": "stub", "action": "get_exercise_summary", "input": kwargs}


# ---------------------------------------------------------------------------
# Stub event handlers
# ---------------------------------------------------------------------------
async def _on_meal_logged(event, session=None):
    """Stub: React to meal_logged — e.g. update daily totals, check goals."""
    pass


async def _on_vitals_recorded(event, session=None):
    """Stub: React to vitals — e.g. detect anomalies, update trends."""
    pass


# ---------------------------------------------------------------------------
# Plugin class
# ---------------------------------------------------------------------------
class HealthPlugin(DomainPlugin):
    """Health & Fitness domain — nutrition, exercise, sleep, vitals."""

    @property
    def domain_id(self) -> str:
        return "health"

    @property
    def name(self) -> str:
        return "Health & Fitness"

    @property
    def version(self) -> str:
        return "0.1.0"

    @property
    def description(self) -> str:
        return "Nutrition, exercise, sleep, vitals, and wellness tracking."

    def get_tools(self) -> list[ToolDeclaration]:
        return [
            ToolDeclaration(
                tool_id="health.log_meal",
                name="Log Meal",
                description="Log a meal with food items. Extracts items, estimates calories and macros.",
                handler=_log_meal,
                parameters_schema={
                    "type": "object",
                    "properties": {
                        "meal_type": {"type": "string", "enum": ["breakfast", "lunch", "dinner", "snack"]},
                        "description": {"type": "string", "description": "Natural language meal description"},
                        "items": {"type": "array", "items": {"type": "string"}},
                    },
                    "required": ["description"],
                },
            ),
            ToolDeclaration(
                tool_id="health.log_exercise",
                name="Log Exercise",
                description="Log an exercise session with type, duration, and intensity.",
                handler=_log_exercise,
                parameters_schema={
                    "type": "object",
                    "properties": {
                        "exercise_type": {"type": "string"},
                        "duration_minutes": {"type": "integer"},
                        "intensity": {"type": "string", "enum": ["low", "moderate", "high"]},
                    },
                    "required": ["exercise_type", "duration_minutes"],
                },
            ),
            ToolDeclaration(
                tool_id="health.log_sleep",
                name="Log Sleep",
                description="Log sleep duration and quality.",
                handler=_log_sleep,
                parameters_schema={
                    "type": "object",
                    "properties": {
                        "duration_hours": {"type": "number"},
                        "quality": {"type": "string", "enum": ["poor", "fair", "good", "excellent"]},
                    },
                    "required": ["duration_hours"],
                },
            ),
            ToolDeclaration(
                tool_id="health.get_nutrition_summary",
                name="Get Nutrition Summary",
                description="Get a daily or weekly nutrition summary with calories and macros.",
                handler=_get_nutrition_summary,
                parameters_schema={
                    "type": "object",
                    "properties": {
                        "period": {"type": "string", "enum": ["today", "week", "month"]},
                    },
                },
            ),
            ToolDeclaration(
                tool_id="health.get_exercise_summary",
                name="Get Exercise Summary",
                description="Get an exercise summary for a given period.",
                handler=_get_exercise_summary,
                parameters_schema={
                    "type": "object",
                    "properties": {
                        "period": {"type": "string", "enum": ["today", "week", "month"]},
                    },
                },
            ),
        ]

    def get_agents(self) -> list[AgentDeclaration]:
        return [
            AgentDeclaration(
                agent_type="health.nutrition_coach",
                name="Nutrition Coach",
                description="Logs meals, provides nutrition advice, and tracks dietary goals.",
                system_prompt=(
                    "You are a friendly and knowledgeable nutrition coach. "
                    "Help the user log meals, track calories and macros, and provide "
                    "personalised dietary advice. Always consider the user's dietary "
                    "preferences and allergies from their profile."
                ),
                tools=["health.log_meal", "health.get_nutrition_summary"],
                temperature=0.7,
            ),
            AgentDeclaration(
                agent_type="health.fitness_advisor",
                name="Fitness Advisor",
                description="Logs exercise, tracks fitness goals, and provides workout advice.",
                system_prompt=(
                    "You are a supportive fitness advisor. Help the user log workouts, "
                    "track progress, and suggest exercise plans based on their goals "
                    "and fitness level."
                ),
                tools=["health.log_exercise", "health.get_exercise_summary"],
                temperature=0.7,
            ),
        ]

    def get_event_handlers(self) -> list[EventHandlerDeclaration]:
        return [
            EventHandlerDeclaration(
                event_pattern="health.meal_logged",
                handler=_on_meal_logged,
                description="Update daily nutrition totals and check goals on meal log.",
            ),
            EventHandlerDeclaration(
                event_pattern="health.vitals_recorded",
                handler=_on_vitals_recorded,
                description="Detect anomalies and update health trends on new vitals.",
            ),
        ]

    def get_memory_categories(self) -> list[MemoryCategoryDeclaration]:
        return [
            MemoryCategoryDeclaration(
                category="dietary_preference",
                description="User's dietary preferences (vegetarian, vegan, keto, etc.)",
                example_keys=["diet_type", "meal_preference"],
            ),
            MemoryCategoryDeclaration(
                category="allergy",
                description="Food allergies and intolerances",
                example_keys=["food_allergy", "intolerance"],
            ),
            MemoryCategoryDeclaration(
                category="fitness_goal",
                description="Fitness and health goals",
                example_keys=["calorie_goal", "weight_goal", "exercise_frequency"],
            ),
            MemoryCategoryDeclaration(
                category="health_metric",
                description="Health measurements and baselines",
                example_keys=["weight", "height", "resting_heart_rate"],
            ),
            MemoryCategoryDeclaration(
                category="supplement",
                description="Supplements and medications",
                example_keys=["supplement_name", "dosage"],
            ),
        ]

    def get_router(self):
        from src.domains.health.router import router

        return router


# Singleton instance — imported by the domain loader
plugin = HealthPlugin()
