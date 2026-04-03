import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from database import FinanceDatabase, ai_categorize, ai_categorize_batch
from tools import calculate_budget_allocation, generate_pdf_report
from finance_agent import create_agent, get_shared_db
from langchain_core.messages import HumanMessage
import google.generativeai as genai
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(page_title="FinGenius - AI Finance Advisor", layout="wide", page_icon="💰")

st.markdown("""
<style>
    .main { background-color: #f8f9fa; }
    .stMetric {
        background-color: #ffffff;
        padding: 15px;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
</style>
""", unsafe_allow_html=True)

# ── Shared DB — single instance for the whole app session ─────────────────────
# Uses the same singleton from finance_agent so embeddings are only loaded once.
db = get_shared_db()

# ── Cache the agent so it is NOT re-created on every Streamlit rerun ──────────
@st.cache_resource
def get_agent(api_key: str, model_name: str):
    """Build the LangGraph agent once and reuse it across all chat turns."""
    return create_agent(api_key, model_name)

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.title("⚙️ Configuration")
    api_key = os.getenv("GOOGLE_API_KEY", "")
    if api_key:
        genai.configure(api_key=api_key)
    else:
        st.warning("⚠️ No API Key found. Please set GOOGLE_API_KEY in your .env file.")

    model_choice = st.selectbox(
        "🤖 AI Model Version",
        ["gemini-1.5-flash", "gemini-2.0-flash", "gemini-2.5-flash"],
        index=0,
        help="Use 1.5 Flash if you hit 'Resource Exhausted' or 429 quota errors."
    )

    st.divider()
    st.header("📥 Data Ingestion")
    data_source = st.selectbox("Select Data Source", ["CSV File", "Google Sheets"])

    if data_source == "CSV File":
        uploaded_file = st.file_uploader("Upload Transaction CSV", type="csv")
        if uploaded_file:
            try:
                upload_df = pd.read_csv(uploaded_file)
                col_map = {str(col).lower().strip(): col for col in upload_df.columns}
                req_map = {'date': 'Date', 'description': 'Description', 'amount': 'Amount'}
                found_cols = {target: col_map[source] for source, target in req_map.items() if source in col_map}

                if len(found_cols) == 3:
                    st.info(f"Matched columns: {', '.join(list(found_cols.values()))}")
                    clear_first = st.checkbox("🗑️ Clear existing data before importing", value=False)

                    if st.button("🚀 Process and Save Transactions"):
                        with st.spinner("Categorizing and saving in batches..."):
                            if clear_first:
                                db.clear_all_data()

                            batch_size = 20
                            to_categorize = []
                            processed_data = []

                            for _, row in upload_df.iterrows():
                                desc = row[found_cols['Description']]
                                amt = row[found_cols['Amount']]
                                date_val = row[found_cols['Date']]

                                if 'category' not in col_map or pd.isna(row.get(col_map.get('category'))):
                                    to_categorize.append({"description": desc, "amount": amt, "date": date_val})
                                else:
                                    processed_data.append({
                                        "Date": str(date_val), "Description": desc, "Amount": amt,
                                        "Category": row[col_map['category']], "Confidence": 1.0, "Reasoning": "Manual"
                                    })

                            bulk_model = genai.GenerativeModel(model_choice)

                            for i in range(0, len(to_categorize), batch_size):
                                batch = to_categorize[i:i + batch_size]
                                results = ai_categorize_batch(batch, bulk_model)
                                for res in results:
                                    idx = int(res.get('id', 0))
                                    if idx < len(batch):
                                        item = batch[idx]
                                        processed_data.append({
                                            "Date": str(item['date']), "Description": item['description'],
                                            "Amount": item['amount'],
                                            "Category": res.get('category', 'Shopping'),
                                            "Confidence": res.get('confidence', 0.5),
                                            "Reasoning": res.get('reasoning', 'AI Batch')
                                        })

                            if processed_data:
                                final_df = pd.DataFrame(processed_data)
                                db.add_transactions(final_df)
                                st.success(f"Successfully processed {len(final_df)} transactions!")
                                st.rerun()
                else:
                    st.error("CSV must contain columns similar to: Date, Description, Amount")
            except Exception as e:
                st.error(f"Error processing CSV: {e}")

    elif data_source == "Google Sheets":
        sheet_id = st.text_input("Google Sheet ID")
        if st.button("Connect to Sheets"):
            st.warning("Google Sheets integration requires service account credentials.")

# ── Main Tabs ─────────────────────────────────────────────────────────────────
tab1, tab2, tab3 = st.tabs(["📊 Dashboard", "💬 AI Chat Advisor", "🔧 Data Management"])

with tab1:
    st.title("📈 Financial Dashboard")
    df = db.get_all_transactions()

    if not df.empty:
        col1, col2, col3 = st.columns(3)
        total_income = df[df['amount'] > 0]['amount'].sum()
        total_expense = df[df['amount'] < 0]['amount'].sum()
        net_worth = total_income + total_expense

        col1.metric("Total Income", f"${total_income:,.2f}")
        col2.metric("Total Expenses", f"${abs(total_expense):,.2f}")
        col3.metric("Net Surplus", f"${net_worth:,.2f}", delta=f"${net_worth:,.2f}")

        col_left, col_right = st.columns(2)
        with col_left:
            spending_df = df[df['amount'] < 0].groupby('category')['amount'].sum().abs().reset_index()
            fig_pie = px.pie(spending_df, values='amount', names='category',
                             title="Spending by Category", hole=0.4)
            st.plotly_chart(fig_pie, use_container_width=True)

        with col_right:
            df['Date'] = pd.to_datetime(df['date'], errors='coerce')
            mask = df['Date'].isna()
            if mask.any():
                df.loc[mask, 'Date'] = pd.to_datetime(df.loc[mask, 'date'], dayfirst=True, errors='coerce')
            monthly_df = df.dropna(subset=['Date']).copy()
            monthly_df['Month'] = monthly_df['Date'].dt.to_period('M').astype(str)
            monthly_trend = monthly_df.groupby('Month')['amount'].sum().reset_index()
            fig_bar = px.bar(monthly_trend, x='Month', y='amount', title="Monthly Net Savings",
                             color='amount', color_continuous_scale='RdYlGn')
            st.plotly_chart(fig_bar, use_container_width=True)

        st.subheader("Recent Transactions")
        st.dataframe(df[['date', 'description', 'amount', 'category', 'confidence']].head(10),
                     use_container_width=True)

        if st.button("📥 Export PDF Report"):
            summary_df = db.get_summary_by_category()
            pdf_file = generate_pdf_report(summary_df)
            with open(pdf_file, "rb") as f:
                st.download_button("Download Report", f, file_name="FinGenius_Report.pdf")
    else:
        st.info("No data available. Please upload transactions in the sidebar or generate sample data in Data Management.")

with tab2:
    st.title("💬 Chat with FinGenius Advisor")

    # ── Conversation history cap to avoid token bloat ─────────────────────────
    MAX_HISTORY = 10  # keep last 10 message pairs = 20 messages

    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Render chat history
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if prompt := st.chat_input("Ask about your finances..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        if api_key:
            try:
                # ✅ Reuse cached agent — no re-init, no new embeddings
                agent = get_agent(api_key, model_choice)

                # ✅ Only send last MAX_HISTORY messages to the agent to save tokens
                recent_messages = st.session_state.messages[-(MAX_HISTORY * 2):]
                lc_messages = [
                    HumanMessage(content=m["content"]) if m["role"] == "user"
                    else HumanMessage(content=f"Assistant: {m['content']}")
                    for m in recent_messages
                ]

                with st.spinner("FinGenius is analyzing your data..."):
                    response = agent.invoke({"messages": lc_messages, "db": db})
                    last_msg = response["messages"][-1]
                    bot_reply = last_msg.content

                    if isinstance(bot_reply, list):
                        parts = []
                        for part in bot_reply:
                            if isinstance(part, dict) and 'text' in part:
                                parts.append(part['text'])
                            elif isinstance(part, str):
                                parts.append(part)
                            elif hasattr(part, 'text'):
                                parts.append(part.text)
                        bot_reply = " ".join(parts)
                    elif not isinstance(bot_reply, str):
                        bot_reply = str(bot_reply)

                with st.chat_message("assistant"):
                    st.markdown(bot_reply)
                st.session_state.messages.append({"role": "assistant", "content": bot_reply})

            except Exception as e:
                err = str(e)
                if "429" in err or "quota" in err.lower() or "exhausted" in err.lower():
                    st.error(
                        "⚠️ **API quota limit reached.** Try these fixes:\n"
                        "- Switch to **gemini-1.5-flash** in the sidebar (lowest quota usage)\n"
                        "- Wait a minute and try again\n"
                        "- Check your [Google AI Studio quota](https://aistudio.google.com/)"
                    )
                else:
                    st.error(f"Agent Error: {err}")
        else:
            st.error("Please enter your Google API Key in the sidebar to chat.")

with tab3:
    st.title("⚙️ Data Management")
    colA, colB = st.columns(2)

    with colA:
        st.subheader("Generate Sample Data")
        if st.button("Generate 3 Months of Sample Data"):
            import random
            categories = ['Groceries', 'Dining', 'Transportation', 'Shopping', 'Entertainment',
                          'Utilities', 'Housing', 'Healthcare', 'Education', 'Income']
            data = []
            for i in range(220):
                d = (datetime.now() - timedelta(days=random.randint(0, 90))).strftime('%d-%m-%Y')
                cat = random.choice(categories)
                amt = random.uniform(20, 500) if cat != 'Income' else random.uniform(1000, 3000)
                if cat != 'Income': amt = -amt
                data.append({"Date": d, "Description": f"Sample {cat}", "Amount": amt, "Category": cat})

            sample_df = pd.DataFrame(data)
            db.add_transactions(sample_df)
            st.success("Sample data generated!")
            st.rerun()

    with colB:
        st.subheader("Clear Database")
        if st.button("🗑️ Delete All Data"):
            db.clear_all_data()
            st.success("All transaction data has been cleared from the database.")
            st.rerun()

# NOTE: db.close() removed — the shared singleton manages its own lifecycle
