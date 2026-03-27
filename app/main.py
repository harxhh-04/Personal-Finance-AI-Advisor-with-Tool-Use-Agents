import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime

from agents.finance_agent import finance_agent # finance_agent(query: str, memory_obj=None)
# ---------- Streamlit Page Config ----------
st.set_page_config(
    page_title="Finance AI Advisor",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ---------- Custom CSS ----------
st.markdown(
    """
<style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&display=swap');
    html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; }
    .main { background-color: #F7F8FC; }

    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1A1A2E 0%, #16213E 100%);
    }
    section[data-testid="stSidebar"] * { color: #E0E0E0 !important; }

    .kpi-card {
        background: white;
        border-radius: 16px;
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
        max-width: 75%; margin-left: auto;
        font-size: 14px;
    }
    .bot-bubble {
        background: white; color: #1A1A2E;
        border-radius: 18px 18px 18px 4px;
        padding: 10px 16px; margin: 6px 0;
        max-width: 75%;
        font-size: 14px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.07);
    }
    .chat-container { padding: 16px; min-height: 400px; overflow-y: auto; }
</style>
""",
    unsafe_allow_html=True,
)

# ---------- Sidebar ----------
with st.sidebar:
    st.markdown("## 💰 Finance AI")
    st.markdown("---")
    page = st.selectbox(
        "Navigate to",
        ["📊 Dashboard", "📋 Transactions", "🤖 Chat Advisor"],
        label_visibility="collapsed",
    )
    st.markdown("---")
    st.markdown("**Team Member:** Member 6\n\n**Role:** Frontend Developer")

# =====================================================================
# 📊 DASHBOARD PAGE
# =====================================================================
if page == "📊 Dashboard":
    st.markdown("## 📊 Spending Overview")
    st.caption("Your financial snapshot at a glance")

    # Try reading from SQLite; if fails, show zeros
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
            this_month = df_dash[df_dash["date"].dt.to_period("M") == pd.Timestamp("today").to_period("M")]

            if not this_month.empty:
                total_spent = this_month["amount"].sum()
                biggest_category = (
                    this_month.groupby("category")["amount"]
                    .sum()
                    .sort_values(ascending=False)
                    .index[0]
                )
        except Exception:
            pass  # keep defaults

    # KPI Row
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(
            f"""
        <div class="kpi-card">
            <div class="kpi-title">Total Spent This Month</div>
            <div class="kpi-value">₹{total_spent:,.0f}</div>
            <div class="kpi-delta">Auto-updates from transactions</div>
        </div>""",
            unsafe_allow_html=True,
        )
    with col2:
        st.markdown(
            f"""
        <div class="kpi-card" style="border-left-color:#F59E0B;">
            <div class="kpi-title">Biggest Category</div>
            <div class="kpi-value">{biggest_category}</div>
            <div class="kpi-delta">Top area of spending</div>
        </div>""",
            unsafe_allow_html=True,
        )
    with col3:
        st.markdown(
            f"""
        <div class="kpi-card" style="border-left-color:#22C55E;">
            <div class="kpi-title">Savings This Month</div>
            <div class="kpi-value">₹{savings_this_month:,.0f}</div>
            <div class="kpi-delta">Estimated from income - expenses</div>
        </div>""",
            unsafe_allow_html=True,
        )

    st.markdown("---")

    col_left, col_right = st.columns(2)
    with col_left:
        st.info("📈 Spending Trend (Line Chart) — wired in Day 5 using transaction data.")
    with col_right:
        st.info("📊 Budget vs Actual (Bar Chart) — wired in Day 5 using Plotly.")

# =====================================================================
# 📋 TRANSACTIONS PAGE
# =====================================================================
elif page == "📋 Transactions":
    st.markdown("## 📋 My Transactions")
    st.caption("View and filter all your transactions")

    db_path = Path("data/finance.db")
    if not db_path.exists():
        st.warning("No database found at data/finance.db")
    else:
        conn = sqlite3.connect(str(db_path))
        df = pd.read_sql("SELECT * FROM transactions", conn)
        conn.close()

        if "date" in df.columns:
            df["date"] = pd.to_datetime(df["date"], errors="coerce")

        # Filter bar
        col1, col2, col3 = st.columns([2, 2, 1])
        with col1:
            selected_date = st.date_input("From date", value=datetime(2025, 1, 1))
        with col2:
            cat_options = (
                ["All"] + sorted(df["category"].dropna().unique().tolist())
                if "category" in df.columns
                else ["All"]
            )
            category = st.selectbox("Category", cat_options)
        with col3:
            st.markdown("<br>", unsafe_allow_html=True)
            filter_btn = st.button("🔍 Filter")

        if filter_btn:
            if "date" in df.columns:
                df = df[df["date"] >= pd.to_datetime(selected_date)]
            if category != "All" and "category" in df.columns:
                df = df[df["category"] == category]

        st.markdown("---")
        st.dataframe(df, use_container_width=True)

        st.download_button(
            label="⬇️ Export to CSV",
            data=df.to_csv(index=False),
            file_name="transactions_export.csv",
            mime="text/csv",
        )

# =====================================================================
# 🤖 CHAT ADVISOR PAGE (WITH MEMORY)
# =====================================================================
elif page == "🤖 Chat Advisor":
    st.markdown("## 🤖 Ask your AI Advisor")
    st.caption("Get personalized financial advice powered by your spending data.")

    # Chat + memory state
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    if "memory_obj" not in st.session_state:
        st.session_state.memory_obj = None  # finance_agent will handle None or you can pass real ConversationBufferMemory

    st.markdown('<div class="chat-container">', unsafe_allow_html=True)

    # Initial welcome
    if not st.session_state.chat_history:
        welcome = "👋 Hello! I’m your Finance AI Advisor. Ask me about your food spend, savings projection, or 50/30/20 rule."
        st.session_state.chat_history.append({"role": "bot", "text": welcome})

    # Render history
    for msg in st.session_state.chat_history:
        if msg["role"] == "user":
            st.markdown(f'<div class="user-bubble">{msg["text"]}</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="bot-bubble">{msg["text"]}</div>', unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)
    st.markdown("---")

    # Text input
    user_input = st.chat_input("Type your question here...")
    if user_input:
        st.session_state.chat_history.append({"role": "user", "text": user_input})

        # Call your memory-enabled agent
        try:
            reply = finance_agent(user_input, memory_obj=st.session_state.memory_obj)
        except TypeError:
            # if your finance_agent only accepts (query)
            reply = finance_agent(user_input)

        st.session_state.chat_history.append({"role": "bot", "text": reply})
        st.rerun()