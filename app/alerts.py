import pandas as pd

# ── Budget limits per category ─────────────────────────────────────────────
BUDGET_LIMITS = {
    "Groceries":              5000,
    "Healthcare":             8000,
    "Education":              5000,
    "Investment & Banking":   15000,
    "Fitness & Sports":       3000,
    "Travel & Accommodation": 8000,
    "Housing & Utilities":    6000,
    "Food & Dining":          6000,
    "Shopping":               5000,
    "Entertainment":          3000,
    "Transport":              3000,
    "Personal Care":          2000,
}

def check_budget_alerts(df, month):
    """
    Compare actual spending to budget for a given month.
    Returns list of alert dicts. level = 'warning' (80-99%) or 'danger' (100%+)
    """
    alerts = []
    month_df = df[df["Month"] == month].copy()

    if month_df.empty:
        return alerts

    actual = month_df.groupby("Category")["Amount"].sum()

    for category, budget in BUDGET_LIMITS.items():
        spent = actual.get(category, 0)
        percent = (spent / budget) * 100

        if percent >= 100:
            alerts.append({
                "category": category,
                "spent": round(spent, 2),
                "budget": budget,
                "percent": round(percent, 1),
                "level": "danger"
            })
        elif percent >= 80:
            alerts.append({
                "category": category,
                "spent": round(spent, 2),
                "budget": budget,
                "percent": round(percent, 1),
                "level": "warning"
            })

    alerts.sort(key=lambda x: x["percent"], reverse=True)
    return alerts
