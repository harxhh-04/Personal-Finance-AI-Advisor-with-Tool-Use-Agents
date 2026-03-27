# =============================================================================
# agents/finance_agent.py - STANDALONE MEMORY (No LangChain needed)
# =============================================================================

class ConversationBufferMemory:
    """Simple memory class for multi-turn chat."""
    def __init__(self):
        self.chat_history = []
    
    def add_user_message(self, message):
        self.chat_history.append({"role": "user", "content": message})
    
    def add_ai_message(self, message):
        self.chat_history.append({"role": "assistant", "content": message})
    
    def get_context(self):
        return self.chat_history[-3:]  # Last 3 exchanges

# Global memory instance
memory = ConversationBufferMemory()

def get_budget_status(category="Food"):
    """Demo budgets."""
    budgets = {
        "Food": "₹5,000 budget | ₹2,847 spent (57%) 🟢 Safe",
        "Transport": "₹3,500 | ₹1,245 (36%) 🟢 Safe", 
        "Entertainment": "₹2,000 | ₹820 (41%) 🟢 Safe"
    }
    return budgets.get(category, "₹3,000 | ₹1,200 (40%) 🟢 Safe")

def calculate_savings_projection(months=6):
    return f"Income ₹28,500/mo | Savings ₹9,300/mo × {months} = ₹55,800 🎯"

def get_financial_advice(topic="budget"):
    advice = {
        "budget": "50/30/20 RULE: 50% needs, 30% wants, 20% savings/debt",
        "savings": "Automate 20% → savings first. Emergency fund = 6 months expenses"
    }
    return advice.get(topic, "Track daily spending!")

def finance_agent(query: str, memory_obj=None) -> str:
    """Memory-enabled agent."""
    if memory_obj is None:
        memory_obj = memory
    
    # Add to memory
    memory_obj.add_user_message(query)
    
    context = memory_obj.get_context()
    q = query.lower()
    
    # Memory-aware responses
    if any(word in q for word in ['budget', 'spend', 'food']):
        result = get_budget_status("Food" if 'food' in q else "Transport")
        if any("food" in msg["content"].lower() for msg in context):
            result += " (as you asked earlier)"
        return result
    
    elif any(word in q for word in ['afford', 'vacation', 'buy']):
        budget = get_budget_status("Entertainment")
        return f"{budget}\n✅ Yes - fits Entertainment budget!"
    
    elif 'save' in q or 'projection' in q:
        return calculate_savings_projection(6)
    
    elif '50/30/20' in q or 'rule' in q:
        return "50/30/20 RULE: 50% needs, 30% wants, 20% savings"
    
    else:
        return f"💰 Quick overview:\n{get_budget_status('Food')}\nAsk: budget/save/afford/50/30/20"
    
    # Add response to memory
    memory_obj.add_ai_message(response)
    return response

# Test
if __name__ == "__main__":
    print("🧠 Agent test:")
    print(finance_agent("food budget"))
    print(finance_agent("compare to last month"))