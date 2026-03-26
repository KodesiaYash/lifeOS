"""
Home & Environment domain manifest — declares tools, agents, events, and workflows.
"""

MANIFEST = {
    "domain_id": "home",
    "name": "Home & Environment",
    "version": "0.1.0",
    "description": "Household tasks, maintenance, inventory, and smart home integrations.",
    "event_types": [
        "home.task_created",
        "home.task_completed",
        "home.maintenance_due",
        "home.inventory_updated",
        "home.shopping_list_updated",
    ],
    "tools": [
        "home.create_task",
        "home.complete_task",
        "home.add_to_shopping_list",
        "home.get_maintenance_schedule",
    ],
    "agents": [
        "home.household_manager",
    ],
    "memory_categories": [
        "home_layout",
        "appliance_info",
        "maintenance_schedule",
        "shopping_preference",
        "household_rule",
    ],
    "workflows": [],
}
