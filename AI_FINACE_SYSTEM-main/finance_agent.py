import os
from typing import TypedDict, Annotated, List, Union
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import BaseMessage, HumanMessage, ToolMessage
from langchain_core.tools import tool
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
import tools
from database import FinanceDatabase

# Global shared DB instance — avoids re-init (and re-embedding) on every tool call
_shared_db: FinanceDatabase = None

def get_shared_db() -> FinanceDatabase:
    global _shared_db
    if _shared_db is None:
        _shared_db = FinanceDatabase()
    return _shared_db

# State definition
class AgentState(TypedDict):
    messages: Annotated[List[BaseMessage], lambda x, y: x + y]
    db: FinanceDatabase

def get_model(api_key: str, model_name: str = "gemini-1.5-flash"):
    """Initializes the Gemini model. Always defaults to 1.5-flash to save quota."""
    try:
        model = ChatGoogleGenerativeAI(
            model=model_name,
            google_api_key=api_key,
            temperature=0.7
        )
        return model
    except Exception:
        return ChatGoogleGenerativeAI(model="gemini-1.5-flash", google_api_key=api_key)

# ── Tools (all reuse shared DB — no new embeddings on each call) ──────────────

@tool
def calculate_budget(monthly_income: float):
    """Calculates budget allocation based on the 50/30/20 rule."""
    return tools.calculate_budget_allocation(monthly_income)

@tool
def calculate_emergency_fund(monthly_expenses: float, months: int = 6):
    """Calculates recommended emergency fund amount (default 6 months)."""
    return tools.calculate_emergency_fund(monthly_expenses, months)

@tool
def calculate_debt_payoff(principal: float, annual_interest_rate: float, monthly_payment: float):
    """Calculates time to pay off debt and total interest."""
    return tools.calculate_debt_payoff(principal, annual_interest_rate, monthly_payment)

@tool
def calculate_investment(principal: float, annual_return: float, years: int, monthly_contribution: float = 0):
    """Calculates future value of an investment."""
    return tools.calculate_investment_growth(principal, annual_return, years, monthly_contribution)

@tool
def calculate_loan(principal: float, annual_interest_rate: float, years: int):
    """Calculates monthly payment for a loan."""
    return tools.calculate_loan_payment(principal, annual_interest_rate, years)

@tool
def get_advice(query: str):
    """Retrieves evidence-based financial advice from the knowledge base."""
    # Uses shared DB — no new ChromaDB/embedding init
    return tools.get_financial_advice(query, get_shared_db())

@tool
def list_transactions(limit: int = 50):
    """Lists the user's most recent transactions. Use this to analyze spending habits."""
    return tools.get_user_transactions(get_shared_db(), limit)

@tool
def summarize_spending():
    """Provides a summary of spending by category. Use this for high-level budget analysis."""
    return tools.get_spending_summary(get_shared_db())


# ── Agent factory — cached via st.cache_resource in app.py ───────────────────

def create_agent(api_key: str, model_name: str = "gemini-1.5-flash"):
    model = get_model(api_key, model_name)
    tool_list = [
        calculate_budget, calculate_emergency_fund,
        calculate_debt_payoff, calculate_investment,
        calculate_loan, get_advice,
        list_transactions, summarize_spending
    ]
    model_with_tools = model.bind_tools(tool_list)

    system_prompt = """You are FinGenius, a personal finance AI advisor.
    Your goal is to help users manage their money, save more, and understand their spending habits.

    When a user asks about THEIR money, spending, or financial situation:
    1. USE the `list_transactions` or `summarize_spending` tools to see what they have done.
    2. Analyze the data to find patterns (e.g., "You spend a lot on Dining").
    3. Provide actionable advice (e.g., "If you reduce Dining by 20%, you could save $X more per month").

    Always be polite, professional, and data-driven.
    Keep answers concise — do NOT repeat the full transaction list back to the user."""

    def call_model(state: AgentState):
        messages = state['messages']
        # Inject system prompt only once at the start
        if not any(
            isinstance(m, HumanMessage) and m.content.startswith("SYSTEM:")
            for m in messages
        ):
            messages = [HumanMessage(content=f"SYSTEM: {system_prompt}")] + messages
        response = model_with_tools.invoke(messages)
        return {"messages": [response]}

    workflow = StateGraph(AgentState)
    workflow.add_node("agent", call_model)
    workflow.add_node("tools", ToolNode(tool_list))
    workflow.set_entry_point("agent")

    def should_continue(state: AgentState):
        last_message = state['messages'][-1]
        if last_message.tool_calls:
            return "tools"
        return END

    workflow.add_conditional_edges("agent", should_continue)
    workflow.add_edge("tools", "agent")

    return workflow.compile()
