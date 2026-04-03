import pandas as pd
from fpdf import FPDF
from datetime import datetime
from database import FinanceDatabase
import os

def calculate_budget_allocation(monthly_income: float) -> dict:
    """Calculate budget allocation based on the 50/30/20 rule."""
    return {
        "needs": monthly_income * 0.5,
        "wants": monthly_income * 0.3,
        "savings": monthly_income * 0.2
    }

def calculate_emergency_fund(monthly_expenses: float, months: int = 6) -> float:
    """Calculate recommended emergency fund amount."""
    return monthly_expenses * months

def calculate_debt_payoff(principal: float, annual_interest_rate: float, monthly_payment: float) -> dict:
    """Calculate time to pay off debt and total interest paid."""
    monthly_rate = (annual_interest_rate / 100) / 12
    num_payments = 0
    total_interest = 0
    balance = principal
    
    if monthly_payment <= balance * monthly_rate:
        return {"error": "Monthly payment too low to cover interest."}

    while balance > 0:
        interest = balance * monthly_rate
        total_interest += interest
        balance = balance + interest - monthly_payment
        num_payments += 1
        if num_payments > 1200: break # 100 years cap
        
    return {
        "months": num_payments,
        "years": round(num_payments / 12, 2),
        "total_interest": round(total_interest, 2)
    }

def calculate_investment_growth(principal: float, annual_return: float, years: int, monthly_contribution: float = 0) -> dict:
    """Calculate investment growth over time."""
    monthly_rate = (annual_return / 100) / 12
    total_contribution = 0
    balance = principal
    
    for _ in range(int(years * 12)):
        balance = balance * (1 + monthly_rate) + monthly_contribution
        total_contribution += monthly_contribution
        
    return {
        "final_value": round(balance, 2),
        "total_contributions": round(total_contribution, 2),
        "profit": round(balance - principal - total_contribution, 2)
    }

def calculate_loan_payment(principal: float, annual_interest_rate: float, years: int) -> dict:
    """Calculate monthly payment for a loan."""
    n = years * 12
    r = (annual_interest_rate / 100) / 12
    if r == 0:
        payment = principal / n
    else:
        payment = principal * (r * (1 + r)**n) / ((1 + r)**n - 1)
    
    total_cost = payment * n
    return {
        "monthly_payment": round(payment, 2),
        "total_cost": round(total_cost, 2),
        "total_interest": round(total_cost - principal, 2)
    }

def get_financial_advice(query: str, db: FinanceDatabase) -> str:
    """Retrieve financial advice from the knowledge base."""
    docs = db.query_knowledge(query)
    if not docs:
        return "No specific advice found for this query."
    return "\n".join([f"- {doc}" for doc in docs])

def generate_pdf_report(summary_df: pd.DataFrame, filename="financial_report.pdf"):
    """Generates a PDF report from transaction summary."""
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(200, 10, txt="FinGenius Financial Report", ln=True, align='C')
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt=f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", ln=True, align='C')
    
    pdf.ln(10)
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(100, 10, "Category", 1)
    pdf.cell(80, 10, "Total Amount ($)", 1)
    pdf.ln()
    
    pdf.set_font("Arial", size=11)
    for _, row in summary_df.iterrows():
        pdf.cell(100, 10, str(row['category']), 1)
        pdf.cell(80, 10, f"{row['total']:,.2f}", 1)
        pdf.ln()
        
    pdf.output(filename)
    return filename

def get_user_transactions(db: FinanceDatabase, limit: int = 100) -> str:
    """Returns a string representation of recent transactions for the agent to analyze."""
    df = db.get_all_transactions()
    if df.empty:
        return "No transactions found in the database."
    # Just return relevant columns to save tokens
    summary = df[['date', 'description', 'amount', 'category']].head(limit)
    return summary.to_string(index=False)

def get_spending_summary(db: FinanceDatabase) -> str:
    """Returns a category-wise spending summary."""
    df = db.get_summary_by_category()
    if df.empty:
        return "No spending data available."
    return df.to_string(index=False)
