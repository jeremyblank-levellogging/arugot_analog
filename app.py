from datetime import timedelta
from io import StringIO
import pandas as pd
import plotly.express as px
import requests
from requests.auth import HTTPBasicAuth
import streamlit as st

st.set_page_config(
    page_title="Water Level Sensor Dashboard", page_icon="🌊", layout="wide"
)

st.title("🌊 Water Level Sensor Dashboard")


# TTL of 1800 seconds (30 minutes) caches the download to prevent rate-limiting
@st.cache_data(ttl=1800)
def fetch_csv_data():
  csv_url = "https://opendigienvlab.pythonanywhere.com/il.ac.bgu.levintal_water_monitoring_867648049123191_WaterLevelReadings_LL_v1_0.qo"
  auth = HTTPBasicAuth("llvs", "llvs")
  res = requests.get(csv_url, auth=auth)
  res.raise_for_status()
  return res.text


@st.fragment(run_every="1800s")
def render_dashboard():
  try:
    # Get data safely via cache
    csv_text = fetch_csv_data()
    df = pd.read_csv(StringIO(csv_text))

    st.sidebar.success(f"Last Refreshed: {pd.Timestamp.now().strftime('%H:%M:%S')}")

    # Explicitly parse date/time and numeric columns
    df["Time"] = pd.to_datetime(df["Time"], format="%H:%M:%S %d/%m/%Y")
    df["LL"] = pd.to_numeric(df["LL"], errors="coerce")

    # --- SIDEBAR TIME FRAME SELECTOR ---
    st.sidebar.markdown("### Dashboard Controls")
    time_option = st.sidebar.selectbox(
        "Select Time Frame",
        [
            "48 Hours",
            "24 Hours",
            "7 Days",
            "30 Days",
            "All Time",
            "Custom Range",
        ],
        index=0,  # Sets '48 Hours' as the default selection
    )

    max_time = df["Time"].max()
    min_time = df["Time"].min()

    # Filter logic based on user selection
    if time_option == "24 Hours":
      cutoff_time = max_time - pd.Timedelta(hours=24)
      df_filtered = df[df["Time"] >= cutoff_time].sort_values("Time")
    elif time_option == "48 Hours":
      cutoff_time = max_time - pd.Timedelta(hours=48)
      df_filtered = df[df["Time"] >= cutoff_time].sort_values("Time")
    elif time_option == "7 Days":
      cutoff_time = max_time - pd.Timedelta(days=7)
      df_filtered = df[df["Time"] >= cutoff_time].sort_values("Time")
    elif time_option == "30 Days":
      cutoff_time = max_time - pd.Timedelta(days=30)
      df_filtered = df[df["Time"] >= cutoff_time].sort_values("Time")
    elif time_option == "All Time":
      df_filtered = df.sort_values("Time")
    elif time_option == "Custom Range":
      st.sidebar.markdown("#### Choose Date Range")
      default_start = (
          max_time - pd.Timedelta(days=2)
          if max_time - pd.Timedelta(days=2) > min_time
          else min_time
    )
      start_date = st.sidebar.date_input(
          "Start Date",
          value=default_start.date(),
          min_value=min_time.date(),
          max_value=max_time.date(),
      )
      end_date = st.sidebar.date_input(
          "End Date",
          value=max_time.date(),
          min_value=min_time.date(),
          max_value=max_time.date(),
      )

      # Filter between start and end date (inclusive)
      mask = (df["Time"].dt.date >= start_date) & (
          df["Time"].dt.date <= end_date
      )
      df_filtered = df[mask].sort_values("Time")

    # Metrics summary
    col1, col2 = st.columns(2)
    with col1:
      st.metric(f"Readings ({time_option})", len(df_filtered))
    with col2:
      if not df_filtered.empty:
        st.metric("Latest LL Value", f"{df_filtered['LL'].iloc[-1]:.2f}")

    # Graph rendering
    if df_filtered.empty:
      st.warning("No data points found within the selected time frame.")
    else:
      title_suffix = (
          f"Custom Range ({start_date} to {end_date})"
          if time_option == "Custom Range"
          else f"Past {time_option}"
      )
      fig = px.line(
          df_filtered,
          x="Time",
          y="LL",
          markers=True,
          template="plotly_white",
          title=f"Water Level (LL) - {title_suffix}",
      )
      fig.update_yaxes(range=[0, 100], title="LL Level")
      fig.update_xaxes(title="Time")
      fig.update_layout(hovermode="x unified")
      st.plotly_chart(fig, use_container_width=True)

    with st.expander("View Filtered Data Table"):
      st.dataframe(df_filtered, use_container_width=True)

  except Exception as e:
    st.error(
        f"Failed to fetch water sensor data (Server might be rate-limiting): {e}"
    )


render_dashboard()
