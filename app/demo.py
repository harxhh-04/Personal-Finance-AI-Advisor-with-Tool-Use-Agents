import streamlit as st
import plotly.express as px
import pandas as pd

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(page_title="Personal Finance Dashboard", page_icon="💰", layout="wide")
st.title("💰 Personal Finance AI Advisor")
st.markdown("---")

# ── Load CSV ──────────────────────────────────────────────────────────────────
df = pd.read_csv("data/updated_transactions.csv")

# Fix date column (DD-MM-YYYY format)
df["Date"] = pd.to_datetime(df["Date"], dayfirst=True)

# Amount is negative — convert to positive for chart readability
df["Amount"] = df["Amount"].abs()

# ── Chart 1: Bar chart — Total Spending per Category ─────────────────────────
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
    color_continuous_scale="Blues",
)
fig1.update_layout(xaxis_tickangle=-30, coloraxis_showscale=False)
st.plotly_chart(fig1, use_container_width=True)

st.divider()

# ── Chart 2: Line chart — Monthly Spending Over Time ─────────────────────────
st.subheader("📈 Monthly Spending Trend")

monthly_df = df.groupby("Month")["Amount"].sum().reset_index()
monthly_df = monthly_df.sort_values("Month")

fig2 = px.line(
    monthly_df,
    x="Month",
    y="Amount",
    title="Total Spending per Month",
    labels={"Amount": "Total Spent (₹)", "Month": "Month"},
    markers=True,
)
fig2.update_traces(line_color="#4F46E5", marker=dict(size=8, color="#4F46E5"))
st.plotly_chart(fig2, use_container_width=True)


