"""Services for the Dutch tutor domain."""

from __future__ import annotations

import re
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession

from src.memory.service import GENERAL_MEMORY_NAMESPACE, MemoryService

NAME_RE = re.compile(r"\bmy name is (?P<value>[A-Za-z][A-Za-z '\-]{1,40})\b", re.IGNORECASE)
NATIVE_LANGUAGE_RE = re.compile(
    r"\bmy native language is (?P<value>[A-Za-z][A-Za-z '\-]{1,40})\b",
    re.IGNORECASE,
)
EXPLANATION_LANGUAGE_RE = re.compile(
    r"\b(?:explain in|use)\s+(?P<value>english|dutch)\b",
    re.IGNORECASE,
)
CEFR_LEVEL_RE = re.compile(
    r"\b(?:my dutch level is|i am|i'm)\s*(?P<value>A1|A2|B1|B2|C1|C2)\b",
    re.IGNORECASE,
)
FOCUS_RE = re.compile(
    r"\b(?:i want to practice|help me with|focus on)\s+(?P<value>grammar|vocabulary|speaking|writing|listening|pronunciation)\b",
    re.IGNORECASE,
)
EXAM_RE = re.compile(
    r"\b(?:i am preparing for|i'm preparing for|help me prepare for)\s+(?P<value>knm|inburgering|nt2)\b",
    re.IGNORECASE,
)
CORRECTION_STYLE_RE = re.compile(
    r"\b(?P<value>correct me strictly|correct me gently|be strict|be gentle|more corrections|less corrections)\b",
    re.IGNORECASE,
)
WORD_RE = re.compile(r"^[A-Za-zÀ-ÿ][A-Za-zÀ-ÿ'\-]{0,40}$")

DUTCH_TO_ENGLISH = {
    "appel": "apple",
    "avond": "evening",
    "antwoord": "answer",
    "blij": "happy",
    "boek": "book",
    "brood": "bread",
    "deur": "door",
    "fiets": "bicycle",
    "gisteren": "yesterday",
    "groot": "big",
    "hond": "dog",
    "huis": "house",
    "kaas": "cheese",
    "kat": "cat",
    "klein": "small",
    "koffie": "coffee",
    "langzaam": "slow",
    "leren": "learn",
    "maan": "moon",
    "melk": "milk",
    "mooi": "beautiful",
    "morgen": "tomorrow",
    "ochtend": "morning",
    "raam": "window",
    "school": "school",
    "snel": "fast",
    "stad": "city",
    "stoel": "chair",
    "taal": "language",
    "tafel": "table",
    "thee": "tea",
    "trein": "train",
    "vraag": "question",
    "vriend": "friend",
    "vuur": "fire",
    "vandaag": "today",
    "water": "water",
    "werk": "work",
    "zon": "sun",
}
ENGLISH_TO_DUTCH = {english: dutch for dutch, english in DUTCH_TO_ENGLISH.items()}


@dataclass(frozen=True)
class TranslationRoundTrip:
    input_word: str
    detected_language: str
    dutch_word: str
    english_word: str
    back_to_dutch: str
    known_word: bool

    @property
    def reply_text(self) -> str:
        if not self.known_word:
            return (
                "Ik ken dit woord nog niet in mijn lokale woordenlijst. "
                "Stuur een eenvoudig Nederlands woord zoals 'huis', 'boek' of 'water'."
            )

        source_label = "Nederlands" if self.detected_language == "dutch" else "English"
        return (
            f"{source_label}: {self.input_word}\n"
            f"English: {self.english_word}\n"
            f"Back to Dutch: {self.back_to_dutch}"
        )


class DutchTutorService:
    """Deterministic word translation and domain-specific memory capture."""

    domain_id = "dutch_tutor"
    general_namespace = GENERAL_MEMORY_NAMESPACE

    @staticmethod
    def normalize_word(word: str) -> str:
        return word.strip().lower()

    @classmethod
    def should_translate_directly(cls, message: str) -> bool:
        stripped = message.strip()
        return bool(stripped) and bool(WORD_RE.fullmatch(stripped))

    @classmethod
    def translate_roundtrip(cls, word: str) -> TranslationRoundTrip:
        normalized = cls.normalize_word(word)
        if normalized in DUTCH_TO_ENGLISH:
            english = DUTCH_TO_ENGLISH[normalized]
            return TranslationRoundTrip(
                input_word=normalized,
                detected_language="dutch",
                dutch_word=normalized,
                english_word=english,
                back_to_dutch=ENGLISH_TO_DUTCH.get(english, normalized),
                known_word=True,
            )

        if normalized in ENGLISH_TO_DUTCH:
            dutch = ENGLISH_TO_DUTCH[normalized]
            english = DUTCH_TO_ENGLISH[dutch]
            return TranslationRoundTrip(
                input_word=normalized,
                detected_language="english",
                dutch_word=dutch,
                english_word=english,
                back_to_dutch=dutch,
                known_word=True,
            )

        return TranslationRoundTrip(
            input_word=normalized,
            detected_language="unknown",
            dutch_word="",
            english_word="",
            back_to_dutch="",
            known_word=False,
        )

    @classmethod
    async def capture_memory(
        cls,
        session: AsyncSession,
        *,
        user_message: str,
        user_name: str | None,
        domain_namespace: str | None = None,
        general_namespace: str = GENERAL_MEMORY_NAMESPACE,
    ) -> None:
        """Persist only stable learner profile and Dutch-study preferences."""
        memory = MemoryService(session)
        domain_namespace = memory.normalize_namespace(domain_namespace or cls.domain_id)
        general_namespace = memory.normalize_namespace(general_namespace)
        lowered = user_message.strip()

        if user_name:
            await memory.upsert_fact(
                namespace=general_namespace,
                category="user_profile",
                key="profile.display_name",
                value=user_name,
                confidence=0.7,
                source="telegram_profile",
            )

        if match := NAME_RE.search(lowered):
            await memory.upsert_fact(
                namespace=general_namespace,
                category="user_profile",
                key="profile.name",
                value=match.group("value").strip(),
                confidence=0.95,
                source="user_stated",
            )

        if match := NATIVE_LANGUAGE_RE.search(lowered):
            await memory.upsert_fact(
                namespace=general_namespace,
                category="user_profile",
                key="profile.native_language",
                value=match.group("value").strip(),
                confidence=0.95,
                source="user_stated",
            )

        if match := EXPLANATION_LANGUAGE_RE.search(lowered):
            await memory.upsert_fact(
                namespace=general_namespace,
                category="learning_preference",
                key="learning.explanation_language",
                value=match.group("value").strip().lower(),
                confidence=0.9,
                source="user_stated",
            )

        if match := CEFR_LEVEL_RE.search(lowered):
            await memory.upsert_fact(
                namespace=domain_namespace,
                category="proficiency",
                key="dutch.cefr_level",
                value=match.group("value").upper(),
                confidence=0.95,
                source="user_stated",
            )

        if match := FOCUS_RE.search(lowered):
            await memory.upsert_fact(
                namespace=domain_namespace,
                category="learning_goal",
                key="dutch.focus_area",
                value=match.group("value").strip().lower(),
                confidence=0.9,
                source="user_stated",
            )

        if match := EXAM_RE.search(lowered):
            await memory.upsert_fact(
                namespace=domain_namespace,
                category="learning_goal",
                key="dutch.exam_target",
                value=match.group("value").strip().lower(),
                confidence=0.9,
                source="user_stated",
            )

        if match := CORRECTION_STYLE_RE.search(lowered):
            await memory.upsert_fact(
                namespace=domain_namespace,
                category="tutor_preference",
                key="dutch.correction_style",
                value=match.group("value").strip().lower(),
                confidence=0.85,
                source="user_stated",
            )
