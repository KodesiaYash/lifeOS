"""
Product requirements for the Relationships domain.

Each requirement has: id, title, description, acceptance_criteria, priority, test_ids.
"""

REQUIREMENTS = [
    {
        "id": "REQ-REL-001",
        "title": "Interaction Logging",
        "description": "User can log interactions with contacts (calls, meetings, messages).",
        "acceptance_criteria": [
            "'I had coffee with Sarah today' triggers relationships.log_interaction",
            "Contact (Sarah), interaction type (meeting), date extracted",
            "Interaction stored with timestamp",
            "Event relationships.interaction_logged emitted",
        ],
        "priority": "P0",
        "test_ids": [],
    },
    {
        "id": "REQ-REL-002",
        "title": "Contact Management",
        "description": "User can create and query contact profiles with relationship context.",
        "acceptance_criteria": [
            "'Add Sarah as a friend, she works at Google' creates a contact",
            "Contact stored with name, relationship type, and notes",
            "Event relationships.contact_created emitted",
        ],
        "priority": "P0",
        "test_ids": [],
    },
    {
        "id": "REQ-REL-003",
        "title": "Interaction History Query",
        "description": "User can ask when they last interacted with a contact.",
        "acceptance_criteria": [
            "'When did I last talk to Mom?' returns last interaction date and type",
            "Response includes context of the interaction",
        ],
        "priority": "P0",
        "test_ids": [],
    },
    {
        "id": "REQ-REL-004",
        "title": "Important Date Reminders",
        "description": "System tracks birthdays, anniversaries, and sends reminders.",
        "acceptance_criteria": [
            "User can set important dates for contacts",
            "Reminder triggered via scheduling module before the date",
            "Event relationships.reminder_due emitted",
        ],
        "priority": "P1",
        "test_ids": [],
    },
]
