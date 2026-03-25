"""
Product requirements for the Health & Fitness domain.

Each requirement is a dict with:
  - id: Unique requirement ID (REQ-HEALTH-xxx)
  - title: Short human-readable title
  - description: Detailed requirement description
  - acceptance_criteria: List of testable conditions
  - priority: P0 (must-have), P1 (should-have), P2 (nice-to-have)
  - test_ids: List of test function paths that verify this requirement
              (populated by arch tests — see tests/arch/test_requirement_coverage.py)
"""

REQUIREMENTS = [
    {
        "id": "REQ-HEALTH-001",
        "title": "Meal Logging via NLP",
        "description": "User can log a meal by describing it in natural language. The system extracts food items, estimates calories and macros, and stores the meal record.",
        "acceptance_criteria": [
            "User message 'I had eggs and toast for breakfast' triggers health.log_meal tool",
            "Extracted items include 'eggs' and 'toast'",
            "Calorie estimate is returned in response",
            "Meal record is persisted with timestamp",
            "Event health.meal_logged is emitted",
        ],
        "priority": "P0",
        "test_ids": [],
    },
    {
        "id": "REQ-HEALTH-002",
        "title": "Exercise Logging",
        "description": "User can log exercise with type, duration, and intensity. System estimates calories burned.",
        "acceptance_criteria": [
            "User message 'I ran for 30 minutes' triggers health.log_exercise tool",
            "Exercise type, duration, and intensity are extracted",
            "Calories burned estimate is returned",
            "Event health.exercise_logged is emitted",
        ],
        "priority": "P0",
        "test_ids": [],
    },
    {
        "id": "REQ-HEALTH-003",
        "title": "Sleep Logging",
        "description": "User can log sleep duration and quality. System tracks sleep patterns over time.",
        "acceptance_criteria": [
            "User message 'I slept 7 hours last night' triggers health.log_sleep tool",
            "Sleep duration is extracted and stored",
            "Event health.sleep_logged is emitted",
        ],
        "priority": "P0",
        "test_ids": [],
    },
    {
        "id": "REQ-HEALTH-004",
        "title": "Nutrition Summary",
        "description": "User can ask for a daily or weekly nutrition summary showing calories, macros, and trends.",
        "acceptance_criteria": [
            "'How many calories today?' triggers health.get_nutrition_summary tool",
            "Response includes total calories consumed",
            "Response includes macro breakdown (protein, carbs, fat)",
            "Response references calorie goal if set",
        ],
        "priority": "P0",
        "test_ids": [],
    },
    {
        "id": "REQ-HEALTH-005",
        "title": "Dietary Preference Memory",
        "description": "System remembers user's dietary preferences (vegetarian, vegan, allergies) and uses them in meal suggestions.",
        "acceptance_criteria": [
            "'I am vegetarian' stores a structured memory fact with category=dietary_preference",
            "Subsequent meal suggestions exclude meat",
            "Memory fact has confidence >= 0.9 when user explicitly states preference",
        ],
        "priority": "P0",
        "test_ids": [],
    },
    {
        "id": "REQ-HEALTH-006",
        "title": "Health Goal Setting",
        "description": "User can set health goals (weight loss, calorie target, exercise frequency).",
        "acceptance_criteria": [
            "'I want to eat 2000 calories per day' creates a health goal",
            "Goal is stored as structured memory fact",
            "Nutrition summaries reference the goal",
            "Event health.goal_set is emitted",
        ],
        "priority": "P1",
        "test_ids": [],
    },
    {
        "id": "REQ-HEALTH-007",
        "title": "Nutrition Coach Agent",
        "description": "A specialised AI agent provides nutrition advice, meal suggestions, and answers health questions using the user's dietary data and preferences.",
        "acceptance_criteria": [
            "Agent health.nutrition_coach is registered with appropriate system prompt",
            "Agent has access to health domain tools",
            "Agent uses user's dietary preferences from memory",
            "Agent provides personalised responses based on meal history",
        ],
        "priority": "P1",
        "test_ids": [],
    },
    {
        "id": "REQ-HEALTH-008",
        "title": "Vitals Recording",
        "description": "User can record vital measurements (weight, blood pressure, heart rate).",
        "acceptance_criteria": [
            "'I weigh 75kg' triggers vitals recording",
            "Measurement is stored with timestamp",
            "Event health.vitals_recorded is emitted",
            "Historical trend is queryable",
        ],
        "priority": "P1",
        "test_ids": [],
    },
]
