"""
Health domain manifest — declares tools, agents, events, and workflows.
"""

MANIFEST = {
    "domain_id": "health",
    "name": "Health & Fitness",
    "version": "0.1.0",
    "description": "Nutrition, exercise, sleep, vitals, and wellness tracking.",
    "event_types": [
        "health.meal_logged",
        "health.exercise_logged",
        "health.sleep_logged",
        "health.vitals_recorded",
        "health.goal_set",
        "health.goal_achieved",
    ],
    "tools": [
        "health.log_meal",
        "health.log_exercise",
        "health.log_sleep",
        "health.get_nutrition_summary",
        "health.get_exercise_summary",
    ],
    "agents": [
        "health.nutrition_coach",
        "health.fitness_advisor",
    ],
    "memory_categories": [
        "dietary_preference",
        "allergy",
        "fitness_goal",
        "health_metric",
        "supplement",
    ],
    "workflows": [],
}
