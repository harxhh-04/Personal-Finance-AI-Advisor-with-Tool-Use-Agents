import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import streamlit as st
import pandas as pd
import plotly.express as px
import sqlite3
from datetime import datetime

# Safe import — won't crash if finance_agent not ready yet
try:
    from agents.finance_agent import finance_agent
    AGENT_AVAILABLE = True
except ImportError:
    AGENT_AVAILABLE = False

# ---------- Page Config ----------
st.set_page_config(
    page_title="Finance AI Advisor",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ---------- Shared Color Palette ----------
COLORS = ["#4F46E5", "#10B981", "#F59E0B", "#EF4444", "#EC4899", "#8B5CF6", "#14B8A6"]

# ---------- Budget Limits ----------
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

# ---------- Custom CSS ----------
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&display=swap');
    html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; }
    .main { background-color: #F7F8FC; }

    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1A1A2E 0%, #16213E 100%);
    }
    section[data-testid="stSidebar"] * { color: #E0E0E0 !important; }

    .kpi-card {
        background: white; border-radius: 16px;
        padding: 24px 20px;
        box-shadow: 0 2px 12px rgba(0,0,0,0.06);
        border-left: 4px solid #6C63FF;
    }
    .kpi-title { font-size: 13px; color: #7A7A9A; font-weight: 600; text-transform: uppercase; letter-spacing: 0.8px; }
    .kpi-value { font-size: 28px; font-weight: 700; color: #1A1A2E; margin-top: 4px; }
    .kpi-delta { font-size: 13px; color: #22C55E; margin-top: 4px; }
    h2 { color: #1A1A2E !important; font-weight: 700 !important; }

    .user-bubble {
        background: #6C63FF; color: white;
        border-radius: 18px 18px 4px 18px;
        padding: 10px 16px; margin: 6px 0;
        max-width: 75%; margin-left: auto; font-size: 14px;
    }
    .bot-bubble {
        background: white; color: #1A1A2E;
        border-radius: 18px 18px 18px 4px;
        padding: 10px 16px; margin: 6px 0;
        max-width: 75%; font-size: 14px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.07);
    }
    .chat-container { padding: 16px; min-height: 400px; overflow-y: auto; }
</style>
""", unsafe_allow_html=True)

# ---------- Load CSV ----------
@st.cache_data
def load_csv():
    # Try updated_transactions first, fallback to sample_transactions
    for fname in ["data/updated_transactions.csv", "data/sample_transactions.csv"]:
        p = Path(fname)
        if p.exists():
            df = pd.read_csv(fname)
            df["Date"] = pd.to_datetime(df["Date"], dayfirst=True)
            df["Amount"] = df["Amount"].abs()
            return df
    return pd.DataFrame()  # empty fallback

csv_df = load_csv()

# ---------- Budget Alert Helper ----------
def check_budget_alerts(df, month):
    alerts = []
    if df.empty or "Month" not in df.columns:
        return alerts
    month_df = df[df["Month"] == month].copy()
    if month_df.empty:
        return alerts
    actual = month_df.groupby("Category")["Amount"].sum()
    for category, budget in BUDGET_LIMITS.items():
        spent = actual.get(category, 0)
        percent = (spent / budget) * 100
        if percent >= 100:
            alerts.append({"category": category, "spent": round(spent, 2),
                           "budget": budget, "percent": round(percent, 1), "level": "danger"})
        elif percent >= 80:
            alerts.append({"category": category, "spent": round(spent, 2),
                           "budget": budget, "percent": round(percent, 1), "level": "warning"})
    alerts.sort(key=lambda x: x["percent"], reverse=True)
    return alerts

# =============================================================
# SIDEBAR
# =============================================================
with st.sidebar:
    st.markdown("## 💰 Finance AI")
    st.markdown("---")
    page = st.selectbox(
        "Navigate to",
        ["📊 Dashboard", "📋 Transactions", "📈 Smart Insights", "🤖 Chat Advisor"],
        label_visibility="collapsed",
    )
    st.markdown("---")

    # Budget Alerts (Day 4)
    st.markdown("### 🔔 Budget Alerts")
    if not csv_df.empty and "Month" in csv_df.columns:
        available_months = sorted(csv_df["Month"].unique().tolist())
        selected_month = st.selectbox("Select Month", available_months)
        alerts = check_budget_alerts(csv_df, selected_month)
        if not alerts:
            st.success("✅ All within budget!")
        else:
            for alert in alerts:
                msg = f"**{alert['category']}** — ₹{alert['spent']:,} / ₹{alert['budget']:,} ({alert['percent']}%)"
                if alert["level"] == "danger":
                    st.error(f"🚨 {msg}")
                else:
                    st.warning(f"⚠️ {msg}")
    else:
        st.info("Load CSV to see alerts.")

    st.markdown("---")
    st.markdown("**Team Member:** Member 7\n\n**Role:** Frontend Developer")


# =============================================================
# 📊 DASHBOARD PAGE  (Member 6 KPIs — kept exactly as-is)
# =============================================================
if page == "📊 Dashboard":
    st.markdown("## 📊 Spending Overview")
    st.caption("Your financial snapshot at a glance")

    total_spent = 0
    biggest_category = "—"
    savings_this_month = 0

    db_path = Path("data/finance.db")
    if db_path.exists():
        try:
            conn = sqlite3.connect(str(db_path))
            df_dash = pd.read_sql("SELECT date, amount, category FROM transactions", conn)
            conn.close()
            df_dash["date"] = pd.to_datetime(df_dash["date"], errors="coerce")
            this_month = df_dash[
                df_dash["date"].dt.to_period("M") == pd.Timestamp("today").to_period("M")
            ]
            if not this_month.empty:
                total_spent = this_month["amount"].sum()
                biggest_category = (
                    this_month.groupby("category")["amount"]
                    .sum().sort_values(ascending=False).index[0]
                )
        except Exception:
            pass

    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-title">Total Spent This Month</div>
            <div class="kpi-value">₹{total_spent:,.0f}</div>
            <div class="kpi-delta">Auto-updates from transactions</div>
        </div>""", unsafe_allow_html=True)
    with col2:
        st.markdown(f"""
        <div class="kpi-card" style="border-left-color:#F59E0B;">
            <div class="kpi-title">Biggest Category</div>
            <div class="kpi-value">{biggest_category}</div>
            <div class="kpi-delta">Top area of spending</div>
        </div>""", unsafe_allow_html=True)
    with col3:
        st.markdown(f"""
        <div class="kpi-card" style="border-left-color:#22C55E;">
            <div class="kpi-title">Savings This Month</div>
            <div class="kpi-value">₹{savings_this_month:,.0f}</div>
            <div class="kpi-delta">Estimated from income - expenses</div>
        </div>""", unsafe_allow_html=True)

    st.markdown("---")

    if csv_df.empty:
        st.warning("CSV not found. Place updated_transactions.csv or sample_transactions.csv in the data/ folder.")
    else:
        # Chart 1 — Spending by Category (demo.py)
        st.subheader("📊 Total Spending by Category")
        cat_df = csv_df.groupby("Category")["Amount"].sum().reset_index()
        cat_df = cat_df.sort_values("Amount", ascending=False)
        fig1 = px.bar(
            cat_df, x="Category", y="Amount",
            title="Total Spending per Category",
            labels={"Amount": "Total Spent (₹)", "Category": "Category"},
            color="Amount", color_continuous_scale="Blues",
        )
        fig1.update_layout(xaxis_tickangle=-30, coloraxis_showscale=False)
        st.plotly_chart(fig1, use_container_width=True)

        st.divider()

        # Chart 2 — Monthly Trend (demo.py)
        st.subheader("📈 Monthly Spending Trend")
        monthly_df = csv_df.groupby("Month")["Amount"].sum().reset_index().sort_values("Month")
        fig2 = px.line(
            monthly_df, x="Month", y="Amount",
            title="Total Spending per Month",
            labels={"Amount": "Total Spent (₹)", "Month": "Month"},
            markers=True,
        )
        fig2.update_traces(line_color="#4F46E5", marker=dict(size=8, color="#4F46E5"))
        st.plotly_chart(fig2, use_container_width=True)


# =============================================================
# 📋 TRANSACTIONS PAGE  (Member 6 — unchanged)
# =============================================================
elif page == "📋 Transactions":
    st.markdown("## 📋 My Transactions")
    st.caption("View and filter all your transactions")

    db_path = Path("data/finance.db")
    if not db_path.exists():
        st.warning("No database found at data/finance.db — showing CSV data instead.")
        df = csv_df.copy()
        date_col, cat_col = "Date", "Category"
    else:
        conn = sqlite3.connect(str(db_path))
        df = pd.read_sql("SELECT * FROM transactions", conn)
        conn.close()
        if "date" in df.columns:
            df["date"] = pd.to_datetime(df["date"], errors="coerce")
        date_col = "date" if "date" in df.columns else "Date"
        cat_col  = "category" if "category" in df.columns else "Category"

    col1, col2, col3 = st.columns([2, 2, 1])
    with col1:
        selected_date = st.date_input("From date", value=datetime(2025, 1, 1))
    with col2:
        cat_options = ["All"] + sorted(df[cat_col].dropna().unique().tolist())
        category = st.selectbox("Category", cat_options)
    with col3:
        st.markdown("<br>", unsafe_allow_html=True)
        filter_btn = st.button("🔍 Filter")

    if filter_btn:
        df = df[df[date_col] >= pd.to_datetime(selected_date)]
        if category != "All":
            df = df[df[cat_col] == category]

    st.markdown("---")
    st.dataframe(df, use_container_width=True)
    st.download_button(
        label="⬇️ Export to CSV",
        data=df.to_csv(index=False),
        file_name="transactions_export.csv",
        mime="text/csv",
    )


# =============================================================
# 📈 SMART INSIGHTS PAGE  (demo.py Charts 3 & 4)
# =============================================================
elif page == "📈 Smart Insights":
    st.markdown("## 📈 Smart Insights Dashboard")
    st.caption("Track spending, compare budgets and plan savings intelligently")
    st.markdown("---")

    if csv_df.empty:
        st.warning("CSV not found. Place updated_transactions.csv or sample_transactions.csv in the data/ folder.")
    else:
        # Chart 3 — Budget vs Actual (demo.py)
        st.subheader("💳 Budget vs Actual Spending")

        budget_data = {
            "Category": ["Food", "Shopping", "Travel", "Bills", "Entertainment"],
            "Budget":   [8000,   6000,       5000,     7000,    4000]
        }
        budget_df = pd.DataFrame(budget_data)
        actual_df = csv_df.groupby("Category")["Amount"].sum().reset_index()
        merge_df  = pd.merge(budget_df, actual_df, on="Category", how="left")
        merge_df["Amount"] = merge_df["Amount"].fillna(0)

        fig3 = px.bar(
            merge_df, x="Category", y=["Budget", "Amount"],
            barmode="group",
            title="Budget vs Actual Spending",
            labels={"value": "Amount (₹)", "variable": "Type"},
            color_discrete_sequence=[COLORS[0], COLORS[1]],
        )
        fig3.update_layout(xaxis_tickangle=-30, legend_title_text="")
        st.plotly_chart(fig3, use_container_width=True)

        st.divider()

        # Chart 4 — Savings Projection (demo.py)
        st.subheader("📈 Savings Projection Over 12 Months")

        months = list(range(1, 13))
        savings_df = pd.DataFrame({
            "Month":       months,
            "₹3k Saving":  [3000  * m for m in months],
            "₹5k Saving":  [5000  * m for m in months],
            "₹10k Saving": [10000 * m for m in months],
        })

        fig4 = px.line(
            savings_df, x="Month",
            y=["₹3k Saving", "₹5k Saving", "₹10k Saving"],
            markers=True,
            title="Savings Projection",
            color_discrete_sequence=[COLORS[2], COLORS[1], COLORS[0]],
        )
        fig4.update_layout(legend_title_text="Monthly Saving")
        st.plotly_chart(fig4, use_container_width=True)


# =============================================================
# 🤖 CHAT ADVISOR PAGE  (Member 6 — unchanged)
# =============================================================
elif page == "🤖 Chat Advisor":
    st.markdown("## 🤖 Ask your AI Advisor")
    st.caption("Get personalized financial advice powered by your spending data.")

    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    if "memory_obj" not in st.session_state:
        st.session_state.memory_obj = None

    st.markdown('<div class="chat-container">', unsafe_allow_html=True)

    if not st.session_state.chat_history:
        welcome = "👋 Hello! I'm your Finance AI Advisor. Ask me about your food spend, savings projection, or 50/30/20 rule."
        st.session_state.chat_history.append({"role": "bot", "text": welcome})

    for msg in st.session_state.chat_history:
        if msg["role"] == "user":
            st.markdown(f'<div class="user-bubble">{msg["text"]}</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="bot-bubble">{msg["text"]}</div>', unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)
    st.markdown("---")

    user_input = st.chat_input("Type your question here...")
    if user_input:
        st.session_state.chat_history.append({"role": "user", "text": user_input})
        if AGENT_AVAILABLE:
            try:
                reply = finance_agent(user_input, memory_obj=st.session_state.memory_obj)
            except TypeError:
                reply = finance_agent(user_input)
        else:
            reply = "⚠️ AI Advisor not available yet — the finance agent module is still being set up by the team."
        st.session_state.chat_history.append({"role": "bot", "text": reply})
        st.rerun()
