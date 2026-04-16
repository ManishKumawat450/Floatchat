import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import sys
import os
import re

from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from backend.sql_generator import ask_floatchat, run_query
from backend.fetcher import fetch_and_ingest
from backend.rag import ask_with_rag, initialize_rag

if "rag_initialized" not in st.session_state:
    initialize_rag()
    st.session_state.rag_initialized = True

# ─────────────────────────────
# Page Config
# ─────────────────────────────
st.set_page_config(
    page_title="FloatChat 🌊",
    page_icon="🌊",
    layout="wide"
)

# ─────────────────────────────
# Custom CSS
# ─────────────────────────────
st.markdown("""
<style>
    .main-title {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1F4E79;
        text-align: center;
    }
    .subtitle {
        font-size: 1rem;
        color: #666;
        text-align: center;
        margin-bottom: 2rem;
    }
    .answer-box {
        background: #E8F4FD;
        border-left: 4px solid #2E75B6;
        padding: 1rem;
        border-radius: 8px;
        margin: 1rem 0;
        color: #1a1a1a;
    }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────
# Header
# ─────────────────────────────
st.markdown('<div class="main-title">🌊 FloatChat</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="subtitle">AI-Powered Conversational Interface for ARGO Ocean Data | INCOIS</div>',
    unsafe_allow_html=True
)
st.divider()

# ─────────────────────────────
# Auto Fetch Function
# ─────────────────────────────
def auto_fetch_if_needed(query: str):
    today_keywords = ['today', 'current', 'latest', 'now']
    if any(k in query.lower() for k in today_keywords):
        fetch_and_ingest(datetime.now())
        return

    date_patterns = [
        r'(\d{2}-\d{2}-\d{4})',
        r'(\d{4}-\d{2}-\d{2})',
    ]
    for pattern in date_patterns:
        match = re.search(pattern, query)
        if match:
            date_str = match.group(1)
            try:
                parts = date_str.split('-')
                if len(parts[0]) == 2 and len(parts[2]) == 4:
                    date = datetime.strptime(date_str, "%d-%m-%Y")
                elif len(parts[0]) == 4:
                    date = datetime.strptime(date_str, "%Y-%m-%d")
                else:
                    continue
                fetch_and_ingest(date)
            except Exception:
                pass

# ─────────────────────────────
# Smart Intent Detection
# ─────────────────────────────
def wants_map(query: str) -> bool:
    keywords = [
        'location', 'map', 'where', 'float location',
        'show float', 'position', 'coordinates', 'locate',
        'find float', 'nearest float'
    ]
    return any(k in query.lower() for k in keywords)

def wants_sql(query: str) -> bool:
    keywords = [
        'sql', 'query', 'code', 'how did you',
        'show query', 'database query'
    ]
    return any(k in query.lower() for k in keywords)

# ─────────────────────────────
# Chart Function
# ─────────────────────────────
def show_chart(df, query=""):
    if df is None or df.empty:
        return

    cols = df.columns.tolist()

    # Dynamic column detection
    temp_col  = next((c for c in cols if 'temp' in c.lower() or c.lower() == 'avg'), None)
    sal_col   = next((c for c in cols if 'sal'  in c.lower()), None)
    date_col  = next((c for c in cols if any(x in c.lower() for x in ['date', 'year', 'month', 'time'])), None)
    pres_col  = next((c for c in cols if 'pres' in c.lower()), None)
    count_col = next((c for c in cols if 'count' in c.lower()), None)

    # Map — sirf tab jab user ne location/map manga ho
    if wants_map(query) and 'latitude' in cols and 'longitude' in cols:
        st.markdown("#### 🗺️ Float Locations")
        df_map = df.drop_duplicates(subset=['latitude', 'longitude'])
        fig = px.scatter_geo(
            df_map,
            lat='latitude',
            lon='longitude',
            hover_data=[c for c in cols if c in df_map.columns],
            title="Argo Float Locations — Indian Ocean",
            color_discrete_sequence=['red']
        )
        fig.update_geos(
            center=dict(lat=15, lon=75),
            projection_scale=4,
            showcountries=True,
            showcoastlines=True,
            showocean=True,
            oceancolor="lightblue",
            showland=True,
            landcolor="lightgreen"
        )
        fig.update_layout(height=400)
        st.plotly_chart(fig, width='stretch')

    # Temperature chart
    if temp_col and date_col:
        st.markdown("#### 🌡️ Temperature Over Time")
        try:
            df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
        except Exception:
            pass

        if 'latitude' in cols and 'longitude' in cols:
            df_plot = df.drop_duplicates(
                subset=[date_col, 'latitude', 'longitude']
            ).sort_values(date_col)
        else:
            df_plot = df.sort_values(date_col)

        unique_times = df_plot[date_col].nunique()
        if unique_times <= 2:
            avg_temp = df[temp_col].mean()
            min_temp = df[temp_col].min()
            max_temp = df[temp_col].max()
            col1, col2, col3 = st.columns(3)
            col1.metric("Average Temperature", f"{avg_temp:.2f}°C")
            col2.metric("Min Temperature",     f"{min_temp:.2f}°C")
            col3.metric("Max Temperature",     f"{max_temp:.2f}°C")
        else:
            fig = px.line(
                df_plot,
                x=date_col,
                y=temp_col,
                title="Ocean Temperature",
                labels={
                    temp_col: 'Temperature (°C)',
                    date_col: 'Date'
                }
            )
            fig.update_traces(line_color='#E8593C', line_width=2)
            fig.update_layout(
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                height=400
            )
            st.plotly_chart(fig, width='stretch')

    # Salinity scatter
    if sal_col and date_col and not temp_col:
        st.markdown("#### 🧂 Salinity Readings")
        try:
            df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
        except Exception:
            pass
        fig = px.scatter(
            df,
            x=date_col,
            y=sal_col,
            title="Ocean Salinity",
            labels={
                sal_col: 'Salinity (PSU)',
                date_col: 'Date'
            }
        )
        fig.update_traces(marker_color='#2E75B6', marker_size=6)
        fig.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            height=400
        )
        st.plotly_chart(fig, width='stretch')

    # Depth profile
    if pres_col and temp_col and not date_col:
        st.markdown("#### 🌊 Depth vs Temperature Profile")
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=df[temp_col],
            y=df[pres_col],
            mode='lines+markers',
            name='Temperature',
            line=dict(color='#E8593C', width=2),
            marker=dict(size=4)
        ))
        fig.update_yaxes(autorange="reversed")
        fig.update_layout(
            title="Temperature vs Depth",
            xaxis_title="Temperature (°C)",
            yaxis_title="Depth (dbar)",
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            height=400
        )
        st.plotly_chart(fig, width='stretch')

    # Count metric
    if count_col and len(df) == 1:
        st.markdown("#### Result")
        st.metric(
            label="Total Count",
            value=f"{int(df[count_col].iloc[0]):,}"
        )

# ─────────────────────────────
# Sidebar
# ─────────────────────────────
with st.sidebar:
    st.markdown("### 🌊 FloatChat")
    st.markdown("INCOIS — Indian Ocean Data Discovery")
    st.divider()

    st.markdown("### 💡 Sample Queries")
    sample_queries = [
        "What is the average temperature in Arabian Sea in 2023?",
        "How many floats are in the Indian Ocean?",
        "Show salinity profiles near equator in January 2024",
        "Show temperature data in Bay of Bengal in 2024",
        "Show float locations in Arabian Sea in 2023",
    ]
    for q in sample_queries:
        if st.button(q, width='stretch'):
            st.session_state.selected_query = q

    st.divider()

# ─────────────────────────────
# Chat History Init
# ─────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg["role"] == "assistant":
            if "sql" in msg and wants_sql(msg.get("query", "")):
                with st.expander("View SQL Query"):
                    st.code(msg["sql"], language="sql")
            if "data" in msg and msg["data"]:
                df = pd.DataFrame(msg["data"])
                if not df.empty:
                    with st.expander("View Raw Data"):
                        st.dataframe(df, width='stretch')
                    show_chart(df, msg.get("query", ""))

# ─────────────────────────────
# Chat Input
# ─────────────────────────────
default_query = st.session_state.get("selected_query", "")
if default_query:
    st.session_state.selected_query = ""

user_input = st.chat_input(
    "Ask about ocean data... (e.g. What is the temperature in Arabian Sea in 2023?)"
)

if user_input or default_query:
    query = user_input or default_query

    st.session_state.messages.append({
        "role"   : "user",
        "content": query
    })
    with st.chat_message("user"):
        st.markdown(query)

    with st.chat_message("assistant"):
        with st.spinner("Checking data availability..."):
            auto_fetch_if_needed(query)

        with st.spinner("Fetching ocean data..."):
            result = ask_with_rag(query)

        # Answer
        st.markdown(
            f'<div class="answer-box">{result["answer"]}</div>',
            unsafe_allow_html=True
        )

        # SQL — sirf tab jab user ne manga ho
        if wants_sql(query):
            with st.expander(" View SQL Query"):
                st.code(result["sql"], language="sql")

        # Data + Charts
        if result["data"] and "error" not in result["data"][0]:
            df = pd.DataFrame(result["data"])
            if not df.empty:
                with st.expander("View Raw Data"):
                    st.dataframe(df, width='stretch')
                show_chart(df, query)
        else:
            st.warning("No data found for this query.")

    st.session_state.messages.append({
        "role"   : "assistant",
        "content": result["answer"],
        "sql"    : result["sql"],
        "data"   : result["data"],
        "query"  : query
    })