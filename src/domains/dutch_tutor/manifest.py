"""Dutch tutor domain manifest."""

MANIFEST = {
    "domain_id": "dutch_tutor",
    "name": "Dutch Tutor",
    "version": "0.1.0",
    "description": "Telegram-first Dutch tutoring with shared and domain-specific memory.",
    "event_types": [
        "dutch_tutor.message_processed",
    ],
    "tools": [
        "dutch_tutor.translate_roundtrip",
    ],
    "agents": [
        "dutch_tutor.translation_coach",
    ],
    "memory_categories": [
        "user_profile",
        "proficiency",
        "learning_goal",
        "tutor_preference",
    ],
    "workflows": [],
}
