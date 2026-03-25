"""
Product requirements for the Finance domain.

Each requirement has: id, title, description, acceptance_criteria, priority, test_ids.
"""

REQUIREMENTS = [
    {
        "id": "REQ-FIN-001",
        "title": "Transaction Logging via NLP",
        "description": "User can log a transaction by describing it naturally. System extracts amount, category, and merchant.",
        "acceptance_criteria": [
            "'I spent $45 on groceries at Whole Foods' triggers finance.log_transaction",
            "Amount ($45), category (groceries), merchant (Whole Foods) extracted",
            "Transaction stored with timestamp",
            "Event finance.transaction_logged emitted",
        ],
        "priority": "P0",
        "test_ids": [],
    },
    {
        "id": "REQ-FIN-002",
        "title": "Spending Summary",
        "description": "User can ask for spending summary by period, showing totals by category.",
        "acceptance_criteria": [
            "'How much did I spend this week?' triggers finance.get_spending_summary",
            "Response includes total amount and breakdown by category",
            "Comparison to previous period provided when available",
        ],
        "priority": "P0",
        "test_ids": [],
    },
    {
        "id": "REQ-FIN-003",
        "title": "Budget Management",
        "description": "User can set monthly budgets by category and track progress.",
        "acceptance_criteria": [
            "'Set my grocery budget to $400/month' creates a budget",
            "Budget status queryable via finance.get_budget_status",
            "Alert emitted when spending exceeds 80% of budget",
            "Event finance.budget_updated emitted",
        ],
        "priority": "P0",
        "test_ids": [],
    },
    {
        "id": "REQ-FIN-004",
        "title": "Financial Goal Setting",
        "description": "User can set savings goals with target amounts and deadlines.",
        "acceptance_criteria": [
            "'I want to save $5000 by December' creates a financial goal",
            "Progress tracked against target",
            "Event finance.goal_set emitted",
        ],
        "priority": "P1",
        "test_ids": [],
    },
    {
        "id": "REQ-FIN-005",
        "title": "Budget Advisor Agent",
        "description": "Specialised agent provides budget advice based on spending patterns and goals.",
        "acceptance_criteria": [
            "Agent finance.budget_advisor registered with finance tools",
            "Provides actionable budget advice based on spending history",
            "References user's financial goals and budget limits",
        ],
        "priority": "P1",
        "test_ids": [],
    },
]
