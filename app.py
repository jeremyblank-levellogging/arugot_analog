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
st.markdown("Showing sensor readings (**LL**) for the last 48 hours.")


@st.fragment(run_even="1800s")
def render_dashboard():
  csv_url = "https://opendigienvlab.pythonanywhere.com/il.ac.bgu.levintal_water_monitoring_867648049123191_WaterLevelReadings_LL_v1_0.qo"
  auth = HTTPBasicAuth("llvs", "llvs")

  try:
    res = requests.get(csv_url, auth=auth)
    res.raise_for_status()

    df = pd.read_csv(StringIO(res.text))

    st.sidebar.success(f"Last Refreshed: {pd.Timestamp.now().strftime('%H:%M:%S')}")

    # Explicitly tell Python how your date/time column is structured
    df["Time"] = pd.to_datetime(df["Time"], format="%H:%M:%S %d/%m/%Y")
    df["LL"] = pd.to_numeric(df["LL"], errors="coerce")

    # Filter for last 48 hours relative to the latest timestamp in the dataset
    cutoff_time = df["Time"].max() - pd.Timedelta(hours=48)
    df_filtered = df[df["Time"] >= cutoff_time].sort_values("Time")

    col1, col2 = st.columns(2)
    with col1:
      st.metric("Readings in Last 48h", len(df_filtered))
    with col2:
      if not df_filtered.empty:
        st.metric("Latest LL Value", f"{df_filtered['LL'].iloc[-1]:.2f}")

    if df_filtered.empty:
      st.warning("No data points found within the last 48 hours.")
    else:
      fig = px.line(
          df_filtered, x="Time", y="LL", markers=True, template="plotly_white"
      )
      fig.update_yaxes(range=[0, 100], title="LL Level")
      fig.update_xaxes(title="Time")
      fig.update_layout(hovermode="x unified")
      st.plotly_chart(fig, use_container_width=True)

    with st.expander("View Filtered Data Table"):
      st.dataframe(df_filtered, use_container_width=True)

  except Exception as e:
    st.error(f"Failed to fetch water sensor data: {e}")


render_dashboard()
