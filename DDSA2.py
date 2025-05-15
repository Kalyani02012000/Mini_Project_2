# === 1. Setup and Imports ===
import streamlit as st
import pandas as pd
import plotly.express as px
import matplotlib.pyplot as plt
import seaborn as sns
import mysql.connector

# === SQL CONNECTION ===
@st.cache_resource
def get_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="1q2w3e",
        database="ddsa"
    )

def load_table(table_name):
    conn = get_connection()
    query = f"SELECT * FROM `{table_name}`"
    return pd.read_sql(query, conn)

# === LOAD REQUIRED TABLES ===
volatility_df = load_table("top_10_volatility")
cumulative_df = load_table("top5_cumulative_return")
sector_df = load_table("sector_wise_performance")
stock_yearly_df = load_table("stocks_yearly_returns")
correlation_matrix = load_table("stock_correlation_matrix")
monthly_returns = load_table("monthly_returns_all_stocks")
top_gainers = load_table("monthly_top_5_gainers")
top_losers = load_table("monthly_top_5_losers")

# === SIDEBAR ===
st.sidebar.title("📊 Stock Market Dashboard")
view = st.sidebar.radio("Select Analysis", [
    "Volatility",
    "Cumulative Return",
    "Sector Return",
    "Stock Correlation",
    "Monthly Gainers & Losers"
])

# === 1. Volatility Bar Chart ===
if view == "Volatility":
    st.title("📉 Top 10 Most Volatile Stocks")

    # Sort by volatility and select top 10
    top_volatility = volatility_df.sort_values("volatility", ascending=False).head(10)

    #Bar chart
    fig = px.bar(
        top_volatility,
        x="ticker",
        y="volatility",
        color="volatility",
        color_continuous_scale="OrRd",
        title="🔝 Top 10 Most Volatile Stocks",
        labels={"ticker": "Stock Ticker", "volatility": "Volatility (Std Dev)"},
        hover_data={"ticker": True, "volatility": ":.2f"}
    )

    fig.update_layout(
        xaxis_title="Stock Ticker",
        yaxis_title="Volatility (Standard Deviation)",
        title_x=0.5,
        plot_bgcolor="#f9f9f9",
        margin=dict(l=40, r=40, t=60, b=40)
    )

    fig.update_traces(marker_line_width=1.5, marker_line_color="black")

    st.plotly_chart(fig)


# === 2. Cumulative Return Chart ===
elif view == "Cumulative Return":
    st.title("📈 Cumulative Returns")
    selected_symbols = st.multiselect("Select Stocks", cumulative_df["ticker"].unique(),
                                      default=cumulative_df["ticker"].unique()[:2])
    
    min_date = pd.to_datetime("2018-01-01")
    max_date = pd.to_datetime("2025-01-01")
    
    date_range = st.slider(
    "Date Range",
    min_value=min_date.to_pydatetime(),
    max_value=max_date.to_pydatetime(),
    value=(min_date.to_pydatetime(), max_date.to_pydatetime())
)

    for symbol in selected_symbols:
      df = load_table(f"{symbol}_cumulative")
    df["date"] = pd.to_datetime(df["date"])
    df = df[(df["date"] >= date_range[0]) & (df["date"] <= date_range[1])]
    df = df.sort_values("date")

    #Area chart
    fig = px.area(
        df,
        x="date",
        y="cumulative_return",
        title=f"{symbol} Cumulative Return"
    )
    st.plotly_chart(fig)

# === 3. Sector-wise Yearly Return Chart ===
elif view == "Sector Return":
    st.title("🏢 Sector Performance")

    show_all = st.checkbox("Show All Sectors", value=True)

    if show_all:
        filtered_sector_df = sector_df.copy()
    else:
        min_val = round(float(sector_df["yearlyreturn"].min()), 2)
        max_val = round(float(sector_df["yearlyreturn"].max()), 2)
        min_return, max_return = st.slider(
            "Filter by Yearly Return",
            min_value=min_val,
            max_value=max_val,
            value=(min_val, max_val)
        )
        filtered_sector_df = sector_df[
            (sector_df["yearlyreturn"] >= min_return) & (sector_df["yearlyreturn"] <= max_return)
        ]

    if filtered_sector_df.empty:
        st.warning("No sectors found within the selected yearly return range.")
    else:
        filtered_sector_df = filtered_sector_df.sort_values(by="yearlyreturn", ascending=False)

        # 📊 Sector Pie Chart
        fig = px.pie(
            filtered_sector_df,
            names="sector",
            values="yearlyreturn",
            title="📊 Sector-wise Return Distribution",
            color_discrete_sequence=px.colors.qualitative.Pastel
        )
        fig.update_traces(
            textinfo="percent+label",
            pull=[0.05] * len(filtered_sector_df)
        )
        st.plotly_chart(fig)

        # ✅ Bar Chart: Stock-wise Yearly Return
        st.subheader("📈 Stock-wise Yearly Return (Bar Chart)")
        sorted_stock_df = stock_yearly_df.sort_values(by="yearlyreturn", ascending=False)

        fig = px.bar(
            sorted_stock_df,
            x="symbol",
            y="yearlyreturn",
            color="sector",
            title="Stock-wise Yearly Returns",
            text="yearlyreturn",
            color_discrete_sequence=px.colors.qualitative.Set3
        )
        fig.update_traces(texttemplate='%{text:.2f}', textposition='outside')
        fig.update_layout(xaxis_tickangle=-45)
        st.plotly_chart(fig)

# === 4. Stock Price Correlation Heatmap ===
elif view == "Stock Correlation":
    st.title("📊 Stock Price Correlation Heatmap")
    tickers = list(correlation_matrix.columns[1:])
    selected_tickers = st.multiselect("Select Stocks to Compare", tickers, default=tickers[:10])
    
    if selected_tickers:
        filtered_df = correlation_matrix[selected_tickers]
        fig, ax = plt.subplots(figsize=(12, 10))
        sns.heatmap(filtered_df.corr(), annot=True, cmap="coolwarm", fmt=".2f")
        st.pyplot(fig)


# === 5. Monthly Top 5 Gainers and Losers ===
elif view == "Monthly Gainers & Losers":
    st.title("📆 Monthly Top 5 Gainers and Losers")
    months = sorted(monthly_returns["month"].unique())
    selected_month = st.selectbox("Select Month", months)

    gainers = top_gainers[top_gainers["month"] == selected_month].sort_values("monthly_return", ascending=True)
    losers = top_losers[top_losers["month"] == selected_month].sort_values("monthly_return", ascending=True)

    col1, col2 = st.columns(2)

    with col1:
        st.subheader(f"📈 {selected_month} - Top 5 Gainers")
        fig_gainers = px.bar(
            gainers,
            x="monthly_return",
            y="symbol",
            orientation="h",
            color="monthly_return",
            color_continuous_scale="Greens",
            labels={"monthly_return": "Monthly Return (%)", "symbol": "Stock"},
            title="Top 5 Monthly Gainers"
        )
        fig_gainers.update_layout(yaxis=dict(title=""), xaxis=dict(title="Return (%)"), title_x=0.5)
        st.plotly_chart(fig_gainers)

    with col2:
        st.subheader(f"📉 {selected_month} - Top 5 Losers")
        fig_losers = px.bar(
            losers,
            x="monthly_return",
            y="symbol",
            orientation="h",
            color="monthly_return",
            color_continuous_scale="Reds",
            labels={"monthly_return": "Monthly Return (%)", "symbol": "Stock"},
            title="Top 5 Monthly Losers"
        )
        fig_losers.update_layout(yaxis=dict(title=""), xaxis=dict(title="Return (%)"), title_x=0.5)
        st.plotly_chart(fig_losers)

