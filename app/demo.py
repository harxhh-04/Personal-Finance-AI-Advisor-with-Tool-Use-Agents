import streamlit as st
import plotly.express as px
import pandas as pd

# ── Page config ─────────────────────────────────────────────
st.set_page_config(page_title="Personal Finance Dashboard", page_icon="💰", layout="wide")

st.title("💰 Personal Finance AI Advisor")
st.markdown("### 📊 Smart Insights Dashboard")
st.caption("Track spending, compare budgets and plan savings intelligently")
st.markdown("---")

# ── Load CSV ────────────────────────────────────────────────
df = pd.read_csv("data/updated_transactions.csv")

df["Date"] = pd.to_datetime(df["Date"], dayfirst=True)
df["Amount"] = df["Amount"].abs()

# ── Chart 1: Spending by Category ───────────────────────────
st.subheader("📊 Total Spending by Category")

cat_df = df.groupby("Category")["Amount"].sum().reset_index()
cat_df = cat_df.sort_values("Amount", ascending=False)

fig1 = px.bar(
    cat_df,
    x="Category",
    y="Amount",
    title="Total Spending per Category",
    labels={"Amount": "Total Spent (₹)", "Category": "Category"},
    color="Amount",
    color_continuous_scale="Blues"
)

fig1.update_layout(xaxis_tickangle=-30, coloraxis_showscale=False)
st.plotly_chart(fig1, use_container_width=True)

st.divider()

# ── Chart 2: Monthly Spending Trend ─────────────────────────
st.subheader("📈 Monthly Spending Trend")

monthly_df = df.groupby("Month")["Amount"].sum().reset_index()
monthly_df = monthly_df.sort_values("Month")

fig2 = px.line(
    monthly_df,
    x="Month",
    y="Amount",
    title="Total Spending per Month",
    labels={"Amount": "Total Spent (₹)", "Month": "Month"},
    markers=True
)

fig2.update_traces(line_color="#4F46E5", marker=dict(size=8, color="#4F46E5"))
st.plotly_chart(fig2, use_container_width=True)

st.divider()

# ── Chart 3: Budget vs Actual ───────────────────────────────
st.subheader("💳 Budget vs Actual Spending")

budget_data = {
    "Category": ["Food", "Shopping", "Travel", "Bills", "Entertainment"],
    "Budget": [8000, 6000, 5000, 7000, 4000]
}

budget_df = pd.DataFrame(budget_data)

actual_df = df.groupby("Category")["Amount"].sum().reset_index()

merge_df = pd.merge(budget_df, actual_df, on="Category", how="left")
merge_df["Amount"] = merge_df["Amount"].fillna(0)

fig3 = px.bar(
    merge_df,
    x="Category",
    y=["Budget", "Amount"],
    barmode="group",
    title="Budget vs Actual Spending",
    labels={"value": "Amount (₹)", "variable": "Type"}
)

st.plotly_chart(fig3, use_container_width=True)

st.divider()

# ── Chart 4: Savings Projection ─────────────────────────────
st.subheader("📈 Savings Projection Over 12 Months")

months = list(range(1, 13))

save_3k = [3000 * m for m in months]
save_5k = [5000 * m for m in months]
save_10k = [10000 * m for m in months]

savings_df = pd.DataFrame({
    "Month": months,
    "₹3k Saving": save_3k,
    "₹5k Saving": save_5k,
    "₹10k Saving": save_10k
})

fig4 = px.line(
    savings_df,
    x="Month",
    y=["₹3k Saving", "₹5k Saving", "₹10k Saving"],
    markers=True,
    title="Savings Projection"
)

st.plotly_chart(fig4, use_container_width=True)
