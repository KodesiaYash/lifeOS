"""
Finance domain manifest — declares tools, agents, events, and workflows.
"""
MANIFEST = {
    "domain_id": "finance",
    "name": "Finance",
    "version": "0.1.0",
    "description": "Transaction tracking, budgets, investments, and financial goals.",
    "event_types": [
        "finance.transaction_logged",
        "finance.budget_updated",
        "finance.investment_updated",
        "finance.goal_set",
        "finance.goal_achieved",
        "finance.alert_triggered",
    ],
    "tools": [
        "finance.log_transaction",
        "finance.get_spending_summary",
        "finance.get_budget_status",
        "finance.get_investment_summary",
    ],
    "agents": [
        "finance.budget_advisor",
    ],
    "memory_categories": [
        "income_source",
        "recurring_expense",
        "financial_goal",
        "investment_preference",
        "budget_rule",
    ],
    "workflows": [],
}
