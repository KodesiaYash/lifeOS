"""
Product requirements for the Home & Environment domain.

Each requirement has: id, title, description, acceptance_criteria, priority, test_ids.
"""

REQUIREMENTS = [
    {
        "id": "REQ-HOME-001",
        "title": "Household Task Management",
        "description": "User can create and complete household tasks.",
        "acceptance_criteria": [
            "'I need to fix the leaky faucet' triggers home.create_task",
            "Task stored with description and status=pending",
            "Event home.task_created emitted",
        ],
        "priority": "P0",
        "test_ids": [],
    },
    {
        "id": "REQ-HOME-002",
        "title": "Shopping List Management",
        "description": "User can add items to and view a shopping list.",
        "acceptance_criteria": [
            "'Add milk and eggs to shopping list' triggers home.add_to_shopping_list",
            "Items added to active shopping list",
            "Event home.shopping_list_updated emitted",
        ],
        "priority": "P0",
        "test_ids": [],
    },
    {
        "id": "REQ-HOME-003",
        "title": "Maintenance Scheduling",
        "description": "System tracks home maintenance schedules and sends reminders.",
        "acceptance_criteria": [
            "User can set recurring maintenance (e.g., 'Change HVAC filter every 3 months')",
            "Reminders triggered via scheduling module",
            "Event home.maintenance_due emitted",
        ],
        "priority": "P1",
        "test_ids": [],
    },
    {
        "id": "REQ-HOME-004",
        "title": "Household Manager Agent",
        "description": "Specialised agent helps manage household tasks and shopping.",
        "acceptance_criteria": [
            "Agent home.household_manager registered with home tools",
            "Can create tasks and manage shopping lists",
            "Provides maintenance schedule summaries",
        ],
        "priority": "P1",
        "test_ids": [],
    },
]
