"""
Finance domain plugin.
Tracks transactions, budgets, investments, and financial goals.
"""
from src.domains.plugin import (
    AgentDeclaration,
    DomainPlugin,
    EventHandlerDeclaration,
    MemoryCategoryDeclaration,
    ToolDeclaration,
)

DOMAIN_ID = "finance"
DOMAIN_NAME = "Finance"
DOMAIN_VERSION = "0.1.0"


# ---------------------------------------------------------------------------
# Stub tool handlers
# ---------------------------------------------------------------------------
async def _log_transaction(**kw):
    return {"status": "stub", "action": "log_transaction", "input": kw}

async def _get_spending_summary(**kw):
    return {"status": "stub", "action": "get_spending_summary", "input": kw}

async def _get_budget_status(**kw):
    return {"status": "stub", "action": "get_budget_status", "input": kw}

async def _get_investment_summary(**kw):
    return {"status": "stub", "action": "get_investment_summary", "input": kw}


# Stub event handlers
async def _on_transaction_logged(event, session=None):
    pass

async def _on_budget_updated(event, session=None):
    pass


class FinancePlugin(DomainPlugin):
    @property
    def domain_id(self) -> str:
        return "finance"

    @property
    def name(self) -> str:
        return "Finance"

    @property
    def version(self) -> str:
        return "0.1.0"

    @property
    def description(self) -> str:
        return "Transaction tracking, budgets, investments, and financial goals."

    def get_tools(self) -> list[ToolDeclaration]:
        return [
            ToolDeclaration(
                tool_id="finance.log_transaction", name="Log Transaction",
                description="Log a financial transaction with amount, category, and merchant.",
                handler=_log_transaction,
                parameters_schema={"type": "object", "properties": {
                    "amount": {"type": "number"}, "category": {"type": "string"},
                    "merchant": {"type": "string"}, "description": {"type": "string"},
                }, "required": ["amount", "description"]},
            ),
            ToolDeclaration(
                tool_id="finance.get_spending_summary", name="Get Spending Summary",
                description="Get spending summary by period with category breakdown.",
                handler=_get_spending_summary,
                parameters_schema={"type": "object", "properties": {
                    "period": {"type": "string", "enum": ["today", "week", "month"]},
                }},
            ),
            ToolDeclaration(
                tool_id="finance.get_budget_status", name="Get Budget Status",
                description="Check current budget utilisation across categories.",
                handler=_get_budget_status,
                parameters_schema={"type": "object", "properties": {
                    "category": {"type": "string"},
                }},
            ),
            ToolDeclaration(
                tool_id="finance.get_investment_summary", name="Get Investment Summary",
                description="Get portfolio summary with returns and allocation.",
                handler=_get_investment_summary,
            ),
        ]

    def get_agents(self) -> list[AgentDeclaration]:
        return [
            AgentDeclaration(
                agent_type="finance.budget_advisor", name="Budget Advisor",
                description="Tracks spending, manages budgets, and provides financial advice.",
                system_prompt=(
                    "You are a practical financial advisor. Help the user track spending, "
                    "manage budgets, and reach financial goals. Be factual and specific."
                ),
                tools=["finance.log_transaction", "finance.get_spending_summary", "finance.get_budget_status"],
            ),
        ]

    def get_event_handlers(self) -> list[EventHandlerDeclaration]:
        return [
            EventHandlerDeclaration(event_pattern="finance.transaction_logged", handler=_on_transaction_logged,
                                    description="Update budget tracking on new transaction."),
            EventHandlerDeclaration(event_pattern="finance.budget_updated", handler=_on_budget_updated,
                                    description="Check budget alerts on budget change."),
        ]

    def get_memory_categories(self) -> list[MemoryCategoryDeclaration]:
        return [
            MemoryCategoryDeclaration(category="income_source", description="User's income sources",
                                      example_keys=["employer", "salary", "frequency"]),
            MemoryCategoryDeclaration(category="recurring_expense", description="Recurring bills and subscriptions",
                                      example_keys=["expense_name", "amount", "frequency"]),
            MemoryCategoryDeclaration(category="financial_goal", description="Savings and financial targets",
                                      example_keys=["goal_name", "target_amount", "deadline"]),
            MemoryCategoryDeclaration(category="investment_preference", description="Investment risk and preferences",
                                      example_keys=["risk_tolerance", "preferred_asset"]),
            MemoryCategoryDeclaration(category="budget_rule", description="Budget rules and limits",
                                      example_keys=["category", "monthly_limit"]),
        ]

    def get_router(self):
        from src.domains.finance.router import router
        return router


plugin = FinancePlugin()
