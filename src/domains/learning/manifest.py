"""
Learning domain manifest — declares tools, agents, events, and workflows.
"""

MANIFEST = {
    "domain_id": "learning",
    "name": "Learning",
    "version": "0.1.0",
    "description": "Courses, reading, skills, certifications, and learning goals.",
    "event_types": [
        "learning.resource_added",
        "learning.session_logged",
        "learning.skill_updated",
        "learning.goal_set",
        "learning.goal_achieved",
        "learning.note_captured",
    ],
    "tools": [
        "learning.add_resource",
        "learning.log_session",
        "learning.get_progress",
        "learning.capture_note",
    ],
    "agents": [
        "learning.tutor",
        "learning.study_planner",
    ],
    "memory_categories": [
        "learning_goal",
        "skill_level",
        "learning_preference",
        "book_note",
        "course_progress",
    ],
    "workflows": [],
}
