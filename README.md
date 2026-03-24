# Personal-Finance-AI-Advisor-with-Tool-Use-Agents

# 💰 Personal Finance AI Advisor

An agentic AI financial advisor that categorizes transactions,
tracks budgets, and provides personalized advice through natural conversation.

## 📁 Project Structure

```
finance-ai-advisor/
├── app/
│   └── main.py              # Streamlit frontend
├── agent/
│   ├── finance_agent.py     # LangChain ReAct agent
│   ├── tools.py             # Agent tools
│   ├── categorize.py        # ML categorization
│   └── rag.py               # RAG pipeline
├── database/
│   ├── schema.sql           # DB schema
│   ├── init_db.py           # DB initializer
│   ├── ingest.py            # Data ingestion
│   └── queries.py           # Query helpers
├── data/
│   ├── sample_transactions.csv
│   ├── sample_user.csv
│   ├── sample_budgets.csv
│   └── rag_docs/            # Financial education PDFs
├── docs/
│   └── architecture.png
├── requirements.txt
└── README.md
```

## 🛠 Tech Stack
- **Frontend**: Streamlit + Plotly
- **AI Agent**: LangChain + LangGraph (ReAct)
- **Categorization**: OpenAI few-shot prompting
- **RAG**: FAISS + LangChain
- **Database**: SQLite
- **Data Source**: CSV (Plaid sandbox fallback)
