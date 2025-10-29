# Import necessary libraries
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Define CSV source (replace with your actual GitHub raw URL)
CSV_URL = "https://raw.githubusercontent.com/oksanalim/bank-transaction-analyzer/refs/heads/main/data/transactions.csv"

@st.cache_data
def load_data():
    """Loads transaction data from GitHub CSV."""
    try:
        df = pd.read_csv(CSV_URL)
        df["transaction_date"] = pd.to_datetime(df["transaction_date"])
        return df
    except Exception as e:
        st.error(f"❌ Failed to load CSV: {e}")
        return pd.DataFrame()  # Return empty DataFrame on error

# Load data
df = load_data()

# Streamlit UI
st.title("💰 Bank Transaction Analyzer")

# Display data in a table
if not df.empty:
    st.dataframe(df)

    # Transactions Over Time
    st.subheader("📊 Transactions Over Time")
    fig, ax = plt.subplots(figsize=(10, 5))
    df.groupby(df["transaction_date"].dt.date)["amount"].sum().plot(
        kind="line", ax=ax, marker="o", color="blue"
    )
    ax.set_title("Total Transaction Amount Over Time")
    ax.set_xlabel("Date")
    ax.set_ylabel("Total Amount")
    ax.grid(True)
    st.pyplot(fig)

    # Category-wise Spending
    st.subheader("📊 Spending by Category")
    if "category_name" in df.columns:
        fig, ax = plt.subplots(figsize=(8, 5))
        sns.barplot(
            x=df.groupby("category_name")["amount"].sum().index,
            y=df.groupby("category_name")["amount"].sum().values,
            ax=ax,
            palette="viridis",
        )
        ax.set_title("Total Spending Per Category")
        ax.set_xlabel("Category")
        ax.set_ylabel("Total Amount")
        plt.xticks(rotation=45)
        st.pyplot(fig)
    else:
        st.warning("⚠️ No category data found.")
else:
    st.warning("⚠️ No transactions found. Please check the data source.")
