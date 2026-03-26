"""
Home & Environment domain plugin.
Manages household tasks, maintenance, inventory, and smart home integrations.
"""

from src.domains.plugin import (
    AgentDeclaration,
    DomainPlugin,
    EventHandlerDeclaration,
    MemoryCategoryDeclaration,
    ToolDeclaration,
)

DOMAIN_ID = "home"
DOMAIN_NAME = "Home & Environment"
DOMAIN_VERSION = "0.1.0"


async def _create_task(**kw):
    return {"status": "stub", "action": "create_task", "input": kw}


async def _complete_task(**kw):
    return {"status": "stub", "action": "complete_task", "input": kw}


async def _add_to_shopping_list(**kw):
    return {"status": "stub", "action": "add_to_shopping_list", "input": kw}


async def _get_maintenance_schedule(**kw):
    return {"status": "stub", "action": "get_maintenance_schedule", "input": kw}


async def _on_task_created(event, session=None):
    pass


async def _on_maintenance_due(event, session=None):
    pass


class HomePlugin(DomainPlugin):
    @property
    def domain_id(self) -> str:
        return "home"

    @property
    def name(self) -> str:
        return "Home & Environment"

    @property
    def version(self) -> str:
        return "0.1.0"

    @property
    def description(self) -> str:
        return "Household tasks, maintenance, inventory, and smart home integrations."

    def get_tools(self) -> list[ToolDeclaration]:
        return [
            ToolDeclaration(
                tool_id="home.create_task",
                name="Create Task",
                description="Create a household task (repair, cleaning, etc.).",
                handler=_create_task,
                parameters_schema={
                    "type": "object",
                    "properties": {
                        "title": {"type": "string"},
                        "category": {"type": "string"},
                        "urgency": {"type": "string", "enum": ["low", "medium", "high"]},
                    },
                    "required": ["title"],
                },
            ),
            ToolDeclaration(
                tool_id="home.complete_task",
                name="Complete Task",
                description="Mark a household task as completed.",
                handler=_complete_task,
                parameters_schema={
                    "type": "object",
                    "properties": {
                        "task_query": {"type": "string"},
                    },
                    "required": ["task_query"],
                },
            ),
            ToolDeclaration(
                tool_id="home.add_to_shopping_list",
                name="Add to Shopping List",
                description="Add items to the household shopping list.",
                handler=_add_to_shopping_list,
                parameters_schema={
                    "type": "object",
                    "properties": {
                        "items": {"type": "array", "items": {"type": "string"}},
                    },
                    "required": ["items"],
                },
            ),
            ToolDeclaration(
                tool_id="home.get_maintenance_schedule",
                name="Get Maintenance Schedule",
                description="View upcoming home maintenance tasks and schedules.",
                handler=_get_maintenance_schedule,
            ),
        ]

    def get_agents(self) -> list[AgentDeclaration]:
        return [
            AgentDeclaration(
                agent_type="home.household_manager",
                name="Household Manager",
                description="Manages household tasks, shopping lists, and maintenance schedules.",
                system_prompt=(
                    "You are a helpful household manager. Help the user track home tasks, "
                    "manage shopping lists, and stay on top of home maintenance."
                ),
                tools=[
                    "home.create_task",
                    "home.complete_task",
                    "home.add_to_shopping_list",
                    "home.get_maintenance_schedule",
                ],
            ),
        ]

    def get_event_handlers(self) -> list[EventHandlerDeclaration]:
        return [
            EventHandlerDeclaration(
                event_pattern="home.task_created",
                handler=_on_task_created,
                description="Update household task dashboard.",
            ),
            EventHandlerDeclaration(
                event_pattern="home.maintenance_due",
                handler=_on_maintenance_due,
                description="Send maintenance reminder notification.",
            ),
        ]

    def get_memory_categories(self) -> list[MemoryCategoryDeclaration]:
        return [
            MemoryCategoryDeclaration(
                category="home_layout", description="Home layout and room info", example_keys=["room", "area_sqft"]
            ),
            MemoryCategoryDeclaration(
                category="appliance_info",
                description="Appliance details and warranties",
                example_keys=["appliance", "brand", "warranty_end"],
            ),
            MemoryCategoryDeclaration(
                category="maintenance_schedule",
                description="Recurring maintenance tasks",
                example_keys=["task", "frequency", "last_done"],
            ),
            MemoryCategoryDeclaration(
                category="shopping_preference",
                description="Shopping preferences and stores",
                example_keys=["preferred_store", "brand_preference"],
            ),
            MemoryCategoryDeclaration(
                category="household_rule", description="Household rules and routines", example_keys=["rule", "schedule"]
            ),
        ]

    def get_router(self):
        from src.domains.home.router import router

        return router


plugin = HomePlugin()
