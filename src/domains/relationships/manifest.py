"""
Relationships domain manifest — declares tools, agents, events, and workflows.
"""
MANIFEST = {
    "domain_id": "relationships",
    "name": "Relationships",
    "version": "0.1.0",
    "description": "Contacts, interactions, relationship health, and social events.",
    "event_types": [
        "relationships.interaction_logged",
        "relationships.contact_created",
        "relationships.event_scheduled",
        "relationships.reminder_due",
    ],
    "tools": [
        "relationships.log_interaction",
        "relationships.create_contact",
        "relationships.get_contact",
        "relationships.schedule_event",
    ],
    "agents": [
        "relationships.social_advisor",
    ],
    "memory_categories": [
        "contact_detail",
        "relationship_note",
        "social_preference",
        "important_date",
    ],
    "workflows": [],
}
