import sqlite3
import pandas as pd
import streamlit as st

st.markdown("### 📋 Transaction Table")

conn = sqlite3.connect("data/finance.db")
df = pd.read_sql("SELECT * FROM transactions", conn)

st.dataframe(df)
