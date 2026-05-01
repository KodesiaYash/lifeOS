"""Product requirements for the Dutch tutor domain."""

REQUIREMENTS = [
    {
        "id": "REQ-DUTCH-001",
        "title": "Roundtrip Word Translation",
        "description": (
            "The Dutch tutor can translate a single Dutch vocabulary word into English and then back into Dutch "
            "through the promoted domain flow."
        ),
        "acceptance_criteria": [
            "A one-word Dutch tutor message routes to the dutch_tutor domain through the communication pipeline",
            "The orchestrator can resolve a direct deterministic tool for the translation use case",
            "The reply shows Dutch -> English -> Dutch roundtrip output",
            "General and dutch_tutor memory remain separately namespaced during retrieval",
        ],
        "priority": "P0",
        "test_ids": [],
    },
]
