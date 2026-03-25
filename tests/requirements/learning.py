"""
Product requirements for the Learning domain.

Each requirement has: id, title, description, acceptance_criteria, priority, test_ids.
"""

REQUIREMENTS = [
    {
        "id": "REQ-LEARN-001",
        "title": "Learning Resource Tracking",
        "description": "User can add books, courses, articles as learning resources.",
        "acceptance_criteria": [
            "'I started reading Deep Work by Cal Newport' triggers learning.add_resource",
            "Resource type (book), title, author extracted and stored",
            "Event learning.resource_added emitted",
        ],
        "priority": "P0",
        "test_ids": [],
    },
    {
        "id": "REQ-LEARN-002",
        "title": "Study Session Logging",
        "description": "User can log study/reading sessions with duration and progress.",
        "acceptance_criteria": [
            "'I read Deep Work for 45 minutes, finished chapter 3' triggers learning.log_session",
            "Duration and progress recorded",
            "Event learning.session_logged emitted",
        ],
        "priority": "P0",
        "test_ids": [],
    },
    {
        "id": "REQ-LEARN-003",
        "title": "Learning Progress Query",
        "description": "User can ask about their learning progress across resources.",
        "acceptance_criteria": [
            "'How is my reading going?' triggers learning.get_progress",
            "Response includes active resources and completion status",
        ],
        "priority": "P0",
        "test_ids": [],
    },
    {
        "id": "REQ-LEARN-004",
        "title": "Note Capture",
        "description": "User can capture notes linked to learning resources.",
        "acceptance_criteria": [
            "Notes are stored and linked to the relevant resource",
            "Notes are searchable via knowledge retrieval",
            "Event learning.note_captured emitted",
        ],
        "priority": "P1",
        "test_ids": [],
    },
    {
        "id": "REQ-LEARN-005",
        "title": "AI Tutor Agent",
        "description": "Specialised agent answers questions about content the user is studying.",
        "acceptance_criteria": [
            "Agent learning.tutor registered with learning tools",
            "Uses knowledge chunks from ingested learning materials",
            "Provides explanations relevant to user's current resource",
        ],
        "priority": "P1",
        "test_ids": [],
    },
]
