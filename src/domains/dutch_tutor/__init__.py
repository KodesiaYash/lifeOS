"""Dutch tutor domain plugin."""

from __future__ import annotations

from typing import TYPE_CHECKING

from src.domains.dutch_tutor.service import DutchTutorService
from src.domains.plugin import (
    AgentDeclaration,
    DomainPlugin,
    EventHandlerDeclaration,
    MemoryCategoryDeclaration,
    ToolDeclaration,
)

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

DOMAIN_ID = "dutch_tutor"
DOMAIN_NAME = "Dutch Tutor"
DOMAIN_VERSION = "0.1.0"

DUTCH_TUTOR_SYSTEM_PROMPT = """You are DutchTutor, a supportive Dutch language tutor for an adult learner.

Core behavior:
- Keep replies concise and practical.
- For single-word translation requests, use the available tool and present Dutch -> English -> Dutch clearly.
- Default to Dutch when helpful, but add a short English note if the learner is struggling.
- Correct gently, explain the most important issue, and keep the learner moving.
- Respect learner profile facts from general memory and Dutch-learning facts from domain memory.
"""


async def _translate_roundtrip(word: str = "") -> dict[str, str | bool]:
    result = DutchTutorService.translate_roundtrip(word)
    return {
        "input_word": result.input_word,
        "detected_language": result.detected_language,
        "dutch_word": result.dutch_word,
        "english_word": result.english_word,
        "back_to_dutch": result.back_to_dutch,
        "known_word": result.known_word,
        "reply_text": result.reply_text,
    }


async def _on_message_processed(event) -> None:
    """Placeholder for future lesson summarisation and spaced-repetition hooks."""
    return None


class DutchTutorPlugin(DomainPlugin):
    @property
    def domain_id(self) -> str:
        return DOMAIN_ID

    @property
    def name(self) -> str:
        return DOMAIN_NAME

    @property
    def version(self) -> str:
        return DOMAIN_VERSION

    @property
    def description(self) -> str:
        return "Telegram-first Dutch tutoring with shared and domain-scoped learner memory."

    def get_tools(self) -> list[ToolDeclaration]:
        return [
            ToolDeclaration(
                tool_id="dutch_tutor.translate_roundtrip",
                name="Translate Word Roundtrip",
                description=(
                    "Translate a single Dutch or English word, then show the roundtrip back into Dutch. "
                    "Use this for quick tutor drills and vocabulary checks."
                ),
                handler=_translate_roundtrip,
                parameters_schema={
                    "type": "object",
                    "properties": {
                        "word": {
                            "type": "string",
                            "description": "A single Dutch or English word to translate.",
                        }
                    },
                    "required": ["word"],
                },
            )
        ]

    def get_agents(self) -> list[AgentDeclaration]:
        return [
            AgentDeclaration(
                agent_type="dutch_tutor.translation_coach",
                name="Dutch Translation Coach",
                description="Helps the learner practice Dutch vocabulary with short, practical feedback.",
                system_prompt=DUTCH_TUTOR_SYSTEM_PROMPT,
                tools=["dutch_tutor.translate_roundtrip"],
                temperature=0.2,
                max_tokens=512,
            )
        ]

    def get_event_handlers(self) -> list[EventHandlerDeclaration]:
        return [
            EventHandlerDeclaration(
                event_pattern="dutch_tutor.message_processed",
                handler=_on_message_processed,
                description="Placeholder for future domain-side follow-up after each Dutch tutor interaction.",
            )
        ]

    def get_memory_categories(self) -> list[MemoryCategoryDeclaration]:
        return [
            MemoryCategoryDeclaration(
                category="user_profile",
                description="Cross-domain learner profile facts reused by the tutor.",
                example_keys=["profile.name", "profile.native_language", "learning.explanation_language"],
            ),
            MemoryCategoryDeclaration(
                category="proficiency",
                description="Dutch-specific proficiency and CEFR tracking.",
                example_keys=["dutch.cefr_level"],
            ),
            MemoryCategoryDeclaration(
                category="learning_goal",
                description="Dutch learning goals, focus areas, and exam targets.",
                example_keys=["dutch.focus_area", "dutch.exam_target"],
            ),
            MemoryCategoryDeclaration(
                category="tutor_preference",
                description="How the learner wants corrections and tutoring delivered.",
                example_keys=["dutch.correction_style"],
            ),
        ]

    def get_router(self):
        from src.domains.dutch_tutor.router import router

        return router

    def resolve_direct_tool(self, user_message: str) -> tuple[str, dict] | None:
        if DutchTutorService.should_translate_directly(user_message):
            return ("dutch_tutor.translate_roundtrip", {"word": user_message.strip()})
        return None

    async def capture_memory(
        self,
        session: AsyncSession,
        *,
        user_message: str,
        user_name: str | None,
        domain_namespace: str | None = None,
        general_namespace: str = "general",
    ) -> None:
        await DutchTutorService.capture_memory(
            session,
            user_message=user_message,
            user_name=user_name,
            domain_namespace=domain_namespace or self.domain_id,
            general_namespace=general_namespace,
        )


plugin = DutchTutorPlugin()
