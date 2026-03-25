"""
Product requirements for the Productivity domain.

Each requirement has: id, title, description, acceptance_criteria, priority, test_ids.
"""

REQUIREMENTS = [
    {
        "id": "REQ-PROD-001",
        "title": "Task Creation via NLP",
        "description": "User can create tasks by describing them naturally. System extracts title, due date, priority.",
        "acceptance_criteria": [
            "'Add a task to call the dentist by Friday' triggers productivity.create_task",
            "Task title, due date (Friday), default priority extracted",
            "Task stored with status=pending",
            "Event productivity.task_created emitted",
        ],
        "priority": "P0",
        "test_ids": [],
    },
    {
        "id": "REQ-PROD-002",
        "title": "Task Completion",
        "description": "User can mark tasks as complete via natural language.",
        "acceptance_criteria": [
            "'Done with the dentist task' triggers productivity.complete_task",
            "Correct task matched and status updated to completed",
            "Event productivity.task_completed emitted",
        ],
        "priority": "P0",
        "test_ids": [],
    },
    {
        "id": "REQ-PROD-003",
        "title": "Task Listing",
        "description": "User can view pending tasks, optionally filtered by project or date.",
        "acceptance_criteria": [
            "'What tasks do I have today?' triggers productivity.list_tasks",
            "Response lists tasks sorted by priority/due date",
            "Overdue tasks highlighted",
        ],
        "priority": "P0",
        "test_ids": [],
    },
    {
        "id": "REQ-PROD-004",
        "title": "Habit Tracking",
        "description": "User can log habit completions and track streaks.",
        "acceptance_criteria": [
            "'I meditated today' triggers productivity.log_habit",
            "Habit record stored with date",
            "Streak count maintained",
            "Event productivity.habit_logged emitted",
        ],
        "priority": "P1",
        "test_ids": [],
    },
    {
        "id": "REQ-PROD-005",
        "title": "Daily Summary",
        "description": "System generates a daily productivity summary with tasks completed, pending, and habits.",
        "acceptance_criteria": [
            "'How was my day?' triggers productivity.get_daily_summary",
            "Summary includes completed/pending task counts",
            "Habits logged today are mentioned",
        ],
        "priority": "P1",
        "test_ids": [],
    },
    {
        "id": "REQ-PROD-006",
        "title": "Planner Agent",
        "description": "Specialised agent helps plan the day/week based on tasks, calendar, and goals.",
        "acceptance_criteria": [
            "Agent productivity.planner registered with productivity tools",
            "Can create a prioritised daily plan from pending tasks",
            "Considers user's work patterns from memory",
        ],
        "priority": "P1",
        "test_ids": [],
    },
]
