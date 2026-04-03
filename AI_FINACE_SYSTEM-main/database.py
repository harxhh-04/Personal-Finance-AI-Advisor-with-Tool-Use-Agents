import os
import sqlite3
import pandas as pd
import chromadb
from chromadb.api import EmbeddingFunction
import google.generativeai as genai
from datetime import datetime
import json
import numpy as np

# Database paths
DB_PATH = "finance_advisor.db"
CHROMA_PATH = "chroma_db"

class GeminiEmbeddingFunction(EmbeddingFunction):
    def __init__(self, model_name="models/embedding-001"):
        self.model_name = model_name

    def __call__(self, input):
        # input is a list of strings
        embeddings = []
        for text in input:
            try:
                result = genai.embed_content(
                    model=self.model_name,
                    content=text,
                    task_type="retrieval_document"
                )
                embeddings.append(result['embedding'])
            except Exception as e:
                print(f"Error getting embedding: {e}")
                embeddings.append([0.0] * 768)
        return embeddings

class FinanceDatabase:
    def __init__(self):
        self.conn = sqlite3.connect(DB_PATH, check_same_thread=False)
        self.create_tables()
        
        # Initialize ChromaDB
        self.chroma_client = chromadb.PersistentClient(path=CHROMA_PATH)
        self.embedding_fn = GeminiEmbeddingFunction()
        self.knowledge_collection = self.chroma_client.get_or_create_collection(
            name="financial_knowledge",
            embedding_function=self.embedding_fn
        )
        self._initialize_knowledge_base()

    def _initialize_knowledge_base(self):
        """Populates the knowledge base with initial financial advice from the notebook."""
        if self.knowledge_collection.count() == 0:
            knowledge = [
                "The 50/30/20 rule suggests allocating 50% of your income to needs, 30% to wants, and 20% to savings and debt repayment.",
                "An emergency fund should ideally cover 3-6 months of essential expenses.",
                "High-interest debt, such as credit card debt, should be prioritized for repayment before investing.",
                "Dollar-cost averaging is an investment strategy where you invest a fixed amount regularly, regardless of market conditions.",
                "A good credit score (above 700) can help you qualify for better interest rates on loans and credit cards.",
                "Diversification in investments helps reduce risk by spreading your money across different asset classes.",
                "Tax-advantaged accounts like 401(k)s and IRAs can help you save for retirement while reducing your tax burden.",
                "Compound interest is the addition of interest to the principal sum of a loan or deposit, resulting in interest earned on interest.",
                "Inflation erodes the purchasing power of money over time, which is why investing is important for long-term financial goals.",
                "A budget is a financial plan that helps you track income and expenses, ensuring you live within your means.",
                "Automating savings and bill payments can help ensure financial consistency and avoid late fees.",
                "The rule of 72 is a simple way to determine how long it will take for an investment to double: divide 72 by the annual rate of return.",
                "Paying yourself first means automatically setting aside a portion of your income for savings before spending on other expenses.",
                "A debt-to-income ratio below 36% is generally considered good for financial health.",
                "Lifestyle inflation occurs when spending increases with income, preventing wealth accumulation despite higher earnings.",
                "Renting can be financially advantageous in certain situations, such as when housing prices are high or when you need flexibility.",
                "Term life insurance is generally more cost-effective than whole life insurance for most people's needs.",
                "A health savings account (HSA) offers triple tax advantages: tax-deductible contributions, tax-free growth, and tax-free withdrawals for qualified medical expenses.",
                "The 4% rule suggests that retirees can withdraw 4% of their retirement savings in the first year, then adjust for inflation each year, with a high probability of not running out of money for at least 30 years.",
                "Zero-based budgeting means allocating every dollar of income to a specific purpose, whether spending, saving, or investing."
            ]
            self.add_knowledge_docs(knowledge, [f"doc_{i}" for i in range(len(knowledge))])
            print(f"Knowledge base pre-populated with {len(knowledge)} entries.")

    def create_tables(self):
        cursor = self.conn.cursor()
        
        # Transactions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT,
                description TEXT,
                amount REAL,
                category TEXT,
                confidence REAL,
                reasoning TEXT,
                source TEXT
            )
        ''')
        
        # Budgets table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS budgets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category TEXT UNIQUE,
                monthly_limit REAL
            )
        ''')
        
        # Users table (simplified)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                email TEXT
            )
        ''')
        
        self.conn.commit()

    def add_transactions(self, df, source="CSV"):
        """Adds a dataframe of transactions to the database, avoiding duplicates."""
        cursor = self.conn.cursor()
        added_count = 0
        for _, row in df.iterrows():
            # Check for existing
            cursor.execute('''
                SELECT id FROM transactions 
                WHERE date = ? AND description = ? AND amount = ?
            ''', (str(row.get('Date')), row.get('Description'), row.get('Amount')))
            
            if not cursor.fetchone():
                cursor.execute('''
                    INSERT INTO transactions (date, description, amount, category, confidence, reasoning, source)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    str(row.get('Date')),
                    row.get('Description'),
                    row.get('Amount'),
                    row.get('Category'),
                    row.get('Confidence', 1.0),
                    row.get('Reasoning', row.get('Reasoning', 'Manual/Provided')),
                    source
                ))
                added_count += 1
        self.conn.commit()
        return added_count

    def get_all_transactions(self):
        return pd.read_sql_query("SELECT * FROM transactions ORDER BY date DESC", self.conn)

    def get_summary_by_category(self, start_date=None, end_date=None):
        query = "SELECT category, SUM(amount) as total FROM transactions"
        params = []
        if start_date and end_date:
            query += " WHERE date BETWEEN ? AND ?"
            params = [start_date, end_date]
        query += " GROUP BY category"
        return pd.read_sql_query(query, self.conn, params=params)

    def set_budget(self, category, limit):
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO budgets (category, monthly_limit)
            VALUES (?, ?)
        ''', (category, limit))
        self.conn.commit()

    def get_budgets(self):
        return pd.read_sql_query("SELECT * FROM budgets", self.conn)

    def add_knowledge_docs(self, docs, ids):
        self.knowledge_collection.add(
            documents=docs,
            ids=ids
        )

    def query_knowledge(self, query_text, n_results=3):
        results = self.knowledge_collection.query(
            query_texts=[query_text],
            n_results=n_results
        )
        return results['documents'][0] if results['documents'] else []

    def clear_all_data(self):
        """Clears all transactions and budgets from the database."""
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM transactions")
        cursor.execute("DELETE FROM budgets")
        self.conn.commit()

    def close(self):
        self.conn.close()

def ai_categorize_batch(transactions, model):
    """Categorizes a list of transactions in a single API call."""
    categories = [
        'Groceries', 'Dining', 'Transportation', 'Shopping', 'Entertainment', 
        'Utilities', 'Housing', 'Healthcare', 'Education', 'Income'
    ]
    
    # Format transactions for the prompt
    tx_list = []
    for i, tx in enumerate(transactions):
        tx_list.append(f"ID:{i} | Desc:{tx['description']} | Amt:{abs(tx['amount']):.2f}")
    
    prompt = f"""
    You are a financial transaction categorizer. Categorize the following transactions into one of these categories:
    {', '.join(categories)}

    Transactions:
    {chr(10).join(tx_list)}

    Provide your response as a JSON array of objects, one for each transaction ID, with:
    - id: The numeric ID provided
    - category: The chosen category
    - confidence: 0-1 score
    - reasoning: brief explanation
    """
    
    try:
        response = model.generate_content(prompt)
        text = response.text
        json_start = text.find('[')
        json_end = text.rfind(']')
        if json_start != -1 and json_end != -1:
            return json.loads(text[json_start:json_end+1])
    except Exception as e:
        print(f"Batch categorization error: {e}")
    
    return []

# Legacy single categorization helper
def ai_categorize(description, amount, model):
    # Just wrap the batch version for compatibility
    res = ai_categorize_batch([{"description": description, "amount": amount}], model)
    if res:
        return res[0]
    return {"category": "Shopping", "confidence": 0.5, "reasoning": "Fallback"}
