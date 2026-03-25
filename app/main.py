import streamlit as st
from app.ui_components import render_kpi_card, render_placeholder_chart, render_chat_message

st.set_page_config(
    page_title="Finance AI Advisor",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ---------- Custom CSS ----------
st.markdown("""
<style>
    /* Global font & background */
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&display=swap');
    html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; }
    .main { background-color: #F7F8FC; }

    /* Sidebar */
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1A1A2E 0%, #16213E 100%);
    }
    section[data-testid="stSidebar"] * { color: #E0E0E0 !important; }
    section[data-testid="stSidebar"] .stSelectbox label { color: #A0A0B0 !important; }

    /* KPI Cards */
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

    /* Section headers */
    h2 { color: #1A1A2E !important; font-weight: 700 !important; }

    /* Chat bubbles */
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
    .quick-btn button {
        background: #EEF0FF !important; color: #6C63FF !important;
        border: 1px solid #C7C4FF !important;
        border-radius: 20px !important; font-size: 13px !important;
    }
</style>
""", unsafe_allow_html=True)

# ---------- Sidebar ----------
with st.sidebar:
    st.markdown("## 💰 Finance AI")
    st.markdown("---")
    page = st.selectbox(
        "Navigate to",
        ["📊 Dashboard", "📋 Transactions", "🤖 Chat Advisor"],
        label_visibility="collapsed"
    )
    st.markdown("---")
    st.markdown("**Team Member:** Member 6\n\n**Role:** Frontend Developer")

# ---------- Page: Dashboard ----------
if page == "📊 Dashboard":
    st.markdown("## 📊 Spending Overview")
    st.caption("Your financial snapshot at a glance")

    # KPI Row
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("""
        <div class="kpi-card">
            <div class="kpi-title">Total Spent This Month</div>
            <div class="kpi-value">₹0</div>
            <div class="kpi-delta">← Data loads on Day 2</div>
        </div>""", unsafe_allow_html=True)
    with col2:
        st.markdown("""
        <div class="kpi-card" style="border-left-color:#F59E0B;">
            <div class="kpi-title">Biggest Category</div>
            <div class="kpi-value">—</div>
            <div class="kpi-delta">← Data loads on Day 2</div>
        </div>""", unsafe_allow_html=True)
    with col3:
        st.markdown("""
        <div class="kpi-card" style="border-left-color:#22C55E;">
            <div class="kpi-title">Savings This Month</div>
            <div class="kpi-value">₹0</div>
            <div class="kpi-delta">← Data loads on Day 2</div>
        </div>""", unsafe_allow_html=True)

    st.markdown("---")

    # Charts placeholder
    col_left, col_right = st.columns(2)
    with col_left:
        st.info("📈 **Spending Trend (Line Chart)** — will be built on Day 5 using Plotly")
    with col_right:
        st.info("📊 **Budget vs Actual (Bar Chart)** — will be built on Day 5 using Plotly")

# ---------- Page: Transactions ----------
elif page == "📋 Transactions":
    st.markdown("## 📋 My Transactions")
    st.caption("View and filter all your transactions")

    import sqlite3
    import pandas as pd

    conn = sqlite3.connect("data/finance.db")
    df = pd.read_sql("SELECT * FROM transactions", conn)

    # ⭐ Filter bar
    col1, col2, col3 = st.columns([2, 2, 1])
    with col1:
        selected_date = st.date_input("From date")
    with col2:
        category = st.selectbox(
            "Category",
            ["All"] + sorted(df["category"].dropna().unique().tolist())
        )
    with col3:
        st.markdown("<br>", unsafe_allow_html=True)
        filter_btn = st.button("🔍 Filter")

    # ⭐ Apply Filter
    if filter_btn:
        df["date"] = pd.to_datetime(df["date"], errors="coerce")

        df = df[df["date"] >= pd.to_datetime(selected_date)]

        if category != "All":
            df = df[df["category"] == category]

    st.markdown("---")

    # ⭐ Show Table
    st.dataframe(df)

    # ⭐ Export
    st.download_button(
        label="⬇️ Export to CSV",
        data=df.to_csv(index=False),
        file_name="transactions_export.csv",
        mime="text/csv"
    )

# ---------- Page: Chat Advisor ----------
elif page == "🤖 Chat Advisor":
    st.markdown("## 🤖 Ask your AI Advisor")
    st.caption("Get personalized financial advice powered by AI")

    # Chat display area
    st.markdown('<div class="chat-container">', unsafe_allow_html=True)

    # Show a welcome message
    st.markdown('<div class="bot-bubble">👋 Hello! I\'m your Finance AI Advisor. I\'ll be fully powered by LangChain on Day 4. For now, ask me anything!</div>', unsafe_allow_html=True)

    # Session state for chat history
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    for msg in st.session_state.chat_history:
        if msg["role"] == "user":
            st.markdown(f'<div class="user-bubble">{msg["text"]}</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="bot-bubble">{msg["text"]}</div>', unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("---")

    # Quick prompts
    st.markdown("**Quick prompts:**")
    qcol1, qcol2, qcol3 = st.columns(3)
    with qcol1:
        if st.button("💬 How am I doing?", key="q1"):
            st.session_state.chat_history.append({"role": "user", "text": "How am I doing?"})
            st.session_state.chat_history.append({"role": "bot", "text": "🔧 Full AI response will be available on Day 4 once LangChain is integrated!"})
            st.rerun()
    with qcol2:
        if st.button("💸 Can I afford ₹5000?", key="q2"):
            st.session_state.chat_history.append({"role": "user", "text": "Can I afford ₹5,000?"})
            st.session_state.chat_history.append({"role": "bot", "text": "🔧 Full AI response will be available on Day 4 once LangChain is integrated!"})
            st.rerun()
    with qcol3:
        if st.button("💡 Where can I save?", key="q3"):
            st.session_state.chat_history.append({"role": "user", "text": "Where can I save?"})
            st.session_state.chat_history.append({"role": "bot", "text": "🔧 Full AI response will be available on Day 4 once LangChain is integrated!"})
            st.rerun()

    # Text input
    user_input = st.chat_input("Type your question here...")
    if user_input:
        st.session_state.chat_history.append({"role": "user", "text": user_input})
        st.session_state.chat_history.append({"role": "bot", "text": "🔧 Full AI integration is coming on Day 4! Your question has been recorded."})
        st.rerun()

