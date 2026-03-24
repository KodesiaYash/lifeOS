"""
Productivity domain manifest — declares tools, agents, events, and workflows.
"""
MANIFEST = {
    "domain_id": "productivity",
    "name": "Productivity",
    "version": "0.1.0",
    "description": "Tasks, projects, goals, habits, and time tracking.",
    "event_types": [
        "productivity.task_created",
        "productivity.task_completed",
        "productivity.project_updated",
        "productivity.habit_logged",
        "productivity.goal_set",
        "productivity.goal_achieved",
        "productivity.time_tracked",
    ],
    "tools": [
        "productivity.create_task",
        "productivity.complete_task",
        "productivity.list_tasks",
        "productivity.log_habit",
        "productivity.get_daily_summary",
    ],
    "agents": [
        "productivity.planner",
        "productivity.focus_coach",
    ],
    "memory_categories": [
        "work_pattern",
        "productivity_goal",
        "project_context",
        "habit_definition",
        "priority_rule",
    ],
    "workflows": [],
}
