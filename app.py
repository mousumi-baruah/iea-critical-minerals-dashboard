import streamlit as st
import pandas as pd
import plotly.express as px

# =================================================
# Page setup
# =================================================
st.set_page_config(layout="wide")
st.title("IEA Critical Minerals: Supply, Demand, and Risk Assessment")

# =================================================
# Load data
# =================================================
@st.cache_data
def load_supply_demand():
    df = pd.read_csv("clean_supply_demand.csv")
    df["mineral"] = df["mineral"].astype(str).str.strip()
    df["scenario"] = df["scenario"].astype(str).str.strip()
    return df

@st.cache_data
def load_summary():
    df = pd.read_csv("supply_demand_summary.csv")
    df["mineral"] = df["mineral"].astype(str).str.strip()
    df["scenario"] = df["scenario"].astype(str).str.strip()
    return df

@st.cache_data
def load_tech_demand():
    df = pd.read_csv("tech_demand.csv")
    df["mineral"] = df["mineral"].astype(str).str.strip()
    df["scenario"] = df["scenario"].astype(str).str.strip()
    df["technology"] = df["technology"].astype(str).str.strip()
    return df

df = load_supply_demand()
summary = load_summary()
tech_df = load_tech_demand()

# =================================================
# Sidebar filters
# =================================================
st.sidebar.header("Filters")

mineral = st.sidebar.selectbox(
    "Select mineral",
    sorted(df["mineral"].unique())
)

scenario = st.sidebar.multiselect(
    "Select scenario",
    sorted(df["scenario"].unique()),
    default=list(df["scenario"].unique())
)

view = st.sidebar.radio(
    "Select view",
    ["Supply vs Demand", "Supply–Demand Gap"]
)

# =================================================
# Filter datasets
# =================================================
filtered = df[
    (df["mineral"] == mineral) &
    (df["scenario"].isin(scenario))
]

summary_filtered = summary[
    (summary["mineral"] == mineral) &
    (summary["scenario"].isin(scenario))
]

base_mineral = mineral.split("-")[0].strip()

tech_filtered = tech_df[
    (tech_df["mineral"].str.contains(base_mineral, case=False, na=False)) &
    (tech_df["scenario"].isin(scenario))
]

# =================================================
# KPI calculations
# =================================================
def safe_min(series):
    return series.min() if series is not None and not series.dropna().empty else None

first_deficit_year = safe_min(summary_filtered.get("first_deficit_year"))
max_deficit = safe_min(summary_filtered.get("max_deficit_kt"))
gap_2030 = safe_min(summary_filtered.get("gap_2030_kt"))
gap_2040 = safe_min(summary_filtered.get("gap_2040_kt"))

# =================================================
# KPI indicators
# =================================================
st.subheader("Key Supply–Demand Risk Indicators")

k1, k2, k3, k4 = st.columns(4)

with k1:
    st.metric("First deficit year", int(first_deficit_year) if first_deficit_year else "No deficit")

with k2:
    st.metric("Maximum deficit (kt)", f"{max_deficit:,.0f}" if max_deficit else "0")

with k3:
    st.metric("Gap in 2030 (kt)", f"{gap_2030:,.0f}" if gap_2030 else "0")

with k4:
    st.metric("Gap in 2040 (kt)", f"{gap_2040:,.0f}" if gap_2040 else "0")

# =================================================
# Main visualization
# =================================================
if view == "Supply vs Demand":
    fig = px.line(
        filtered,
        x="year",
        y=["demand_kt", "supply_kt"],
        markers=True,
        title=f"Supply vs Demand for {mineral}",
        labels={"value": "kt", "year": "Year", "variable": "Metric"}
    )
else:
    fig = px.bar(
        filtered,
        x="year",
        y="gap_kt",
        color="scenario",
        title=f"Supply–Demand Gap for {mineral}",
        labels={"gap_kt": "Supply − Demand (kt)", "year": "Year"}
    )

st.plotly_chart(fig, use_container_width=True)

# =================================================
# Technology drivers (INFORMATIONAL ONLY)
# =================================================
st.subheader("Technology Drivers of Demand")

if tech_filtered.empty:
    st.info(
        "Technology-level demand data is not reported by the IEA for this mineral. "
        "Risk assessment and supply–demand analysis remain valid."
    )
else:
    tech_fig = px.area(
        tech_filtered,
        x="year",
        y="demand_kt",
        color="technology",
        title=f"Technology Drivers of {base_mineral} Demand",
        labels={
            "demand_kt": "Demand (kt)",
            "year": "Year",
            "technology": "Technology"
        }
    )
    st.plotly_chart(tech_fig, use_container_width=True)

# =================================================
# 🔴 MINERAL RISK RANKING — ALWAYS VISIBLE
# =================================================
st.subheader("Mineral Supply Risk Ranking")

rank_scenario = st.selectbox(
    "Scenario for risk ranking",
    sorted(summary["scenario"].unique())
)

ranking = summary[summary["scenario"] == rank_scenario].copy()

ranking["max_deficit_kt"] = ranking["max_deficit_kt"].fillna(0)
ranking["first_deficit_year"] = ranking["first_deficit_year"].fillna(9999)

ranking = ranking.sort_values(
    by=["max_deficit_kt", "first_deficit_year"],
    ascending=[True, True]
)

ranking["risk_rank"] = range(1, len(ranking) + 1)

ranking_display = ranking[
    [
        "risk_rank",
        "mineral",
        "first_deficit_year",
        "max_deficit_kt",
        "gap_2030_kt",
        "gap_2040_kt",
    ]
]

st.dataframe(ranking_display, use_container_width=True)

# =================================================
# Raw data (optional)
# =================================================
with st.expander("Show underlying time-series data"):
    st.dataframe(filtered)
