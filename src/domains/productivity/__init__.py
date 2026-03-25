"""
Productivity domain plugin.
Manages tasks, projects, goals, habits, and time tracking.
"""
from src.domains.plugin import (
    AgentDeclaration,
    DomainPlugin,
    EventHandlerDeclaration,
    MemoryCategoryDeclaration,
    ToolDeclaration,
)

DOMAIN_ID = "productivity"
DOMAIN_NAME = "Productivity"
DOMAIN_VERSION = "0.1.0"


# ---------------------------------------------------------------------------
# Stub tool handlers
# ---------------------------------------------------------------------------
async def _create_task(**kw):
    return {"status": "stub", "action": "create_task", "input": kw}

async def _complete_task(**kw):
    return {"status": "stub", "action": "complete_task", "input": kw}

async def _list_tasks(**kw):
    return {"status": "stub", "action": "list_tasks", "input": kw}

async def _log_habit(**kw):
    return {"status": "stub", "action": "log_habit", "input": kw}

async def _get_daily_summary(**kw):
    return {"status": "stub", "action": "get_daily_summary", "input": kw}


# Stub event handlers
async def _on_task_created(event, session=None):
    pass

async def _on_task_completed(event, session=None):
    pass


class ProductivityPlugin(DomainPlugin):
    @property
    def domain_id(self) -> str:
        return "productivity"

    @property
    def name(self) -> str:
        return "Productivity"

    @property
    def version(self) -> str:
        return "0.1.0"

    @property
    def description(self) -> str:
        return "Tasks, projects, goals, habits, and time tracking."

    def get_tools(self) -> list[ToolDeclaration]:
        return [
            ToolDeclaration(
                tool_id="productivity.create_task", name="Create Task",
                description="Create a new task with title, due date, and priority.",
                handler=_create_task,
                parameters_schema={"type": "object", "properties": {
                    "title": {"type": "string"}, "due_date": {"type": "string"},
                    "priority": {"type": "string", "enum": ["low", "medium", "high"]},
                    "project": {"type": "string"},
                }, "required": ["title"]},
            ),
            ToolDeclaration(
                tool_id="productivity.complete_task", name="Complete Task",
                description="Mark a task as completed by title or ID.",
                handler=_complete_task,
                parameters_schema={"type": "object", "properties": {
                    "task_query": {"type": "string"},
                }, "required": ["task_query"]},
            ),
            ToolDeclaration(
                tool_id="productivity.list_tasks", name="List Tasks",
                description="List pending tasks, optionally filtered by project or date.",
                handler=_list_tasks,
                parameters_schema={"type": "object", "properties": {
                    "filter": {"type": "string", "enum": ["today", "week", "overdue", "all"]},
                    "project": {"type": "string"},
                }},
            ),
            ToolDeclaration(
                tool_id="productivity.log_habit", name="Log Habit",
                description="Log completion of a daily habit.",
                handler=_log_habit,
                parameters_schema={"type": "object", "properties": {
                    "habit_name": {"type": "string"},
                }, "required": ["habit_name"]},
            ),
            ToolDeclaration(
                tool_id="productivity.get_daily_summary", name="Get Daily Summary",
                description="Get productivity summary: tasks completed, pending, habits logged.",
                handler=_get_daily_summary,
            ),
        ]

    def get_agents(self) -> list[AgentDeclaration]:
        return [
            AgentDeclaration(
                agent_type="productivity.planner", name="Planner",
                description="Plans the day/week based on tasks, calendar, and goals.",
                system_prompt=(
                    "You are a productivity planner. Help the user organise tasks, "
                    "prioritise work, and build daily plans. Be action-oriented and concise."
                ),
                tools=["productivity.create_task", "productivity.list_tasks", "productivity.get_daily_summary"],
            ),
            AgentDeclaration(
                agent_type="productivity.focus_coach", name="Focus Coach",
                description="Tracks habits and helps maintain focus and productivity streaks.",
                system_prompt=(
                    "You are a focus and habit coach. Help the user build consistent habits, "
                    "maintain streaks, and stay focused on their goals."
                ),
                tools=["productivity.log_habit", "productivity.get_daily_summary"],
            ),
        ]

    def get_event_handlers(self) -> list[EventHandlerDeclaration]:
        return [
            EventHandlerDeclaration(event_pattern="productivity.task_created", handler=_on_task_created,
                                    description="Update project task count on new task."),
            EventHandlerDeclaration(event_pattern="productivity.task_completed", handler=_on_task_completed,
                                    description="Update streaks and daily summary on task completion."),
        ]

    def get_memory_categories(self) -> list[MemoryCategoryDeclaration]:
        return [
            MemoryCategoryDeclaration(category="work_pattern", description="User's work patterns and preferences",
                                      example_keys=["peak_hours", "work_style"]),
            MemoryCategoryDeclaration(category="productivity_goal", description="Productivity targets",
                                      example_keys=["goal_name", "target"]),
            MemoryCategoryDeclaration(category="project_context", description="Active project context",
                                      example_keys=["project_name", "status"]),
            MemoryCategoryDeclaration(category="habit_definition", description="Defined habits to track",
                                      example_keys=["habit_name", "frequency"]),
            MemoryCategoryDeclaration(category="priority_rule", description="Prioritisation rules",
                                      example_keys=["rule_name", "condition"]),
        ]

    def get_router(self):
        from src.domains.productivity.router import router
        return router


plugin = ProductivityPlugin()
