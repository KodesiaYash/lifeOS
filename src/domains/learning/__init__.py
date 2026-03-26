"""
Learning domain plugin.
Tracks courses, reading, skills, certifications, and learning goals.
"""

from src.domains.plugin import (
    AgentDeclaration,
    DomainPlugin,
    EventHandlerDeclaration,
    MemoryCategoryDeclaration,
    ToolDeclaration,
)

DOMAIN_ID = "learning"
DOMAIN_NAME = "Learning"
DOMAIN_VERSION = "0.1.0"


async def _add_resource(**kw):
    return {"status": "stub", "action": "add_resource", "input": kw}


async def _log_session(**kw):
    return {"status": "stub", "action": "log_session", "input": kw}


async def _get_progress(**kw):
    return {"status": "stub", "action": "get_progress", "input": kw}


async def _capture_note(**kw):
    return {"status": "stub", "action": "capture_note", "input": kw}


async def _on_resource_added(event, session=None):
    pass


async def _on_session_logged(event, session=None):
    pass


class LearningPlugin(DomainPlugin):
    @property
    def domain_id(self) -> str:
        return "learning"

    @property
    def name(self) -> str:
        return "Learning"

    @property
    def version(self) -> str:
        return "0.1.0"

    @property
    def description(self) -> str:
        return "Courses, reading, skills, certifications, and learning goals."

    def get_tools(self) -> list[ToolDeclaration]:
        return [
            ToolDeclaration(
                tool_id="learning.add_resource",
                name="Add Resource",
                description="Add a learning resource (book, course, article).",
                handler=_add_resource,
                parameters_schema={
                    "type": "object",
                    "properties": {
                        "title": {"type": "string"},
                        "resource_type": {"type": "string"},
                        "author": {"type": "string"},
                    },
                    "required": ["title"],
                },
            ),
            ToolDeclaration(
                tool_id="learning.log_session",
                name="Log Session",
                description="Log a study or reading session with duration and progress.",
                handler=_log_session,
                parameters_schema={
                    "type": "object",
                    "properties": {
                        "resource_title": {"type": "string"},
                        "duration_minutes": {"type": "integer"},
                        "progress_note": {"type": "string"},
                    },
                    "required": ["resource_title", "duration_minutes"],
                },
            ),
            ToolDeclaration(
                tool_id="learning.get_progress",
                name="Get Progress",
                description="Get learning progress across active resources.",
                handler=_get_progress,
            ),
            ToolDeclaration(
                tool_id="learning.capture_note",
                name="Capture Note",
                description="Capture a note linked to a learning resource.",
                handler=_capture_note,
                parameters_schema={
                    "type": "object",
                    "properties": {
                        "resource_title": {"type": "string"},
                        "note": {"type": "string"},
                    },
                    "required": ["note"],
                },
            ),
        ]

    def get_agents(self) -> list[AgentDeclaration]:
        return [
            AgentDeclaration(
                agent_type="learning.tutor",
                name="AI Tutor",
                description="Answers questions about content the user is studying.",
                system_prompt=(
                    "You are a knowledgeable tutor. Help the user understand concepts "
                    "from their learning materials. Use their notes and progress context."
                ),
                tools=["learning.get_progress", "learning.capture_note"],
            ),
            AgentDeclaration(
                agent_type="learning.study_planner",
                name="Study Planner",
                description="Plans study schedules and tracks learning goals.",
                system_prompt=(
                    "You are a study planner. Help the user schedule study sessions, "
                    "set learning goals, and maintain consistent progress."
                ),
                tools=["learning.add_resource", "learning.log_session", "learning.get_progress"],
            ),
        ]

    def get_event_handlers(self) -> list[EventHandlerDeclaration]:
        return [
            EventHandlerDeclaration(
                event_pattern="learning.resource_added",
                handler=_on_resource_added,
                description="Index new resource for knowledge retrieval.",
            ),
            EventHandlerDeclaration(
                event_pattern="learning.session_logged",
                handler=_on_session_logged,
                description="Update progress tracking on session completion.",
            ),
        ]

    def get_memory_categories(self) -> list[MemoryCategoryDeclaration]:
        return [
            MemoryCategoryDeclaration(
                category="learning_goal", description="Learning targets", example_keys=["goal_name", "target_date"]
            ),
            MemoryCategoryDeclaration(
                category="skill_level", description="Self-assessed skill levels", example_keys=["skill", "level"]
            ),
            MemoryCategoryDeclaration(
                category="learning_preference",
                description="Learning style preferences",
                example_keys=["preferred_format", "study_time"],
            ),
            MemoryCategoryDeclaration(
                category="book_note",
                description="Notes from books and articles",
                example_keys=["title", "chapter", "key_insight"],
            ),
            MemoryCategoryDeclaration(
                category="course_progress",
                description="Course completion progress",
                example_keys=["course_name", "completion_pct"],
            ),
        ]

    def get_router(self):
        from src.domains.learning.router import router

        return router


plugin = LearningPlugin()
