"""
Relationships domain plugin.
Manages contacts, interactions, and relationship health.
"""

from src.domains.plugin import (
    AgentDeclaration,
    DomainPlugin,
    EventHandlerDeclaration,
    MemoryCategoryDeclaration,
    ToolDeclaration,
)

DOMAIN_ID = "relationships"
DOMAIN_NAME = "Relationships"
DOMAIN_VERSION = "0.1.0"


async def _log_interaction(**kw):
    return {"status": "stub", "action": "log_interaction", "input": kw}


async def _create_contact(**kw):
    return {"status": "stub", "action": "create_contact", "input": kw}


async def _get_contact(**kw):
    return {"status": "stub", "action": "get_contact", "input": kw}


async def _schedule_event(**kw):
    return {"status": "stub", "action": "schedule_event", "input": kw}


async def _on_interaction_logged(event, session=None):
    pass


async def _on_reminder_due(event, session=None):
    pass


class RelationshipsPlugin(DomainPlugin):
    @property
    def domain_id(self) -> str:
        return "relationships"

    @property
    def name(self) -> str:
        return "Relationships"

    @property
    def version(self) -> str:
        return "0.1.0"

    @property
    def description(self) -> str:
        return "Contacts, interactions, relationship health, and social events."

    def get_tools(self) -> list[ToolDeclaration]:
        return [
            ToolDeclaration(
                tool_id="relationships.log_interaction",
                name="Log Interaction",
                description="Log an interaction with a contact (call, meeting, message).",
                handler=_log_interaction,
                parameters_schema={
                    "type": "object",
                    "properties": {
                        "contact_name": {"type": "string"},
                        "interaction_type": {"type": "string"},
                        "description": {"type": "string"},
                    },
                    "required": ["contact_name"],
                },
            ),
            ToolDeclaration(
                tool_id="relationships.create_contact",
                name="Create Contact",
                description="Create a new contact with name, relationship type, and notes.",
                handler=_create_contact,
                parameters_schema={
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "relationship_type": {"type": "string"},
                        "notes": {"type": "string"},
                    },
                    "required": ["name"],
                },
            ),
            ToolDeclaration(
                tool_id="relationships.get_contact",
                name="Get Contact",
                description="Look up a contact and their interaction history.",
                handler=_get_contact,
                parameters_schema={
                    "type": "object",
                    "properties": {
                        "contact_name": {"type": "string"},
                    },
                    "required": ["contact_name"],
                },
            ),
            ToolDeclaration(
                tool_id="relationships.schedule_event",
                name="Schedule Event",
                description="Schedule a social event or reminder for a contact.",
                handler=_schedule_event,
                parameters_schema={
                    "type": "object",
                    "properties": {
                        "contact_name": {"type": "string"},
                        "event_type": {"type": "string"},
                        "date": {"type": "string"},
                    },
                    "required": ["contact_name", "event_type"],
                },
            ),
        ]

    def get_agents(self) -> list[AgentDeclaration]:
        return [
            AgentDeclaration(
                agent_type="relationships.social_advisor",
                name="Social Advisor",
                description="Helps manage relationships, log interactions, and remember important dates.",
                system_prompt=(
                    "You are a thoughtful social advisor. Help the user maintain relationships, "
                    "remember important details about contacts, and suggest ways to stay connected."
                ),
                tools=["relationships.log_interaction", "relationships.get_contact", "relationships.schedule_event"],
            ),
        ]

    def get_event_handlers(self) -> list[EventHandlerDeclaration]:
        return [
            EventHandlerDeclaration(
                event_pattern="relationships.interaction_logged",
                handler=_on_interaction_logged,
                description="Update contact last-interaction timestamp.",
            ),
            EventHandlerDeclaration(
                event_pattern="relationships.reminder_due",
                handler=_on_reminder_due,
                description="Send notification for relationship reminder.",
            ),
        ]

    def get_memory_categories(self) -> list[MemoryCategoryDeclaration]:
        return [
            MemoryCategoryDeclaration(
                category="contact_detail",
                description="Contact details and metadata",
                example_keys=["name", "relationship_type", "workplace"],
            ),
            MemoryCategoryDeclaration(
                category="relationship_note", description="Notes about relationships", example_keys=["topic", "context"]
            ),
            MemoryCategoryDeclaration(
                category="social_preference",
                description="Social preferences",
                example_keys=["communication_style", "meeting_preference"],
            ),
            MemoryCategoryDeclaration(
                category="important_date",
                description="Birthdays, anniversaries, etc.",
                example_keys=["date", "occasion", "contact"],
            ),
        ]

    def get_router(self):
        from src.domains.relationships.router import router

        return router


plugin = RelationshipsPlugin()
