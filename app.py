import streamlit as st
import pandas as pd
import os

# Streamlit page setup
st.set_page_config(page_title="Dry Gas CSV Tool", layout="wide")

# ==========================================================
# Load or create Master CSV
# ==========================================================
MASTER_FILE = "TestData53684.csv"

# Load master file if it exists
if os.path.exists(MASTER_FILE):
    master_df = pd.read_csv(MASTER_FILE)
else:
    master_df = pd.DataFrame()

# Upload replacement master file
uploaded_master = st.sidebar.file_uploader("📂 Upload or Replace Master CSV", type=["csv"])
if uploaded_master is not None:
    master_df = pd.read_csv(uploaded_master)

# If empty, create placeholder with 12 rows
if master_df.empty:
    st.warning("⚠️ No master CSV found — creating empty editable table.")
    master_df = pd.DataFrame(index=range(12))
else:
    # Always display 12 rows minimum
    if len(master_df) < 12:
        extra_rows = 12 - len(master_df)
        empty_rows = pd.DataFrame(index=range(extra_rows))
        master_df = pd.concat([master_df, empty_rows], ignore_index=True)

st.title("💨 Dry Gas CSV Editor & Trend Viewer")

# ==========================================================
# Editable Table
# ==========================================================
st.subheader("✏️ Master CSV (Editable)")

edited_master = st.data_editor(
    master_df,
    num_rows="dynamic",
    use_container_width=True,
    key="editable_master"
)

# ==========================================================
# Save / Download Section
# ==========================================================
st.download_button(
    "💾 Download Updated CSV",
    edited_master.to_csv(index=False),
    "Updated_Master.csv",
    mime="text/csv"
)

# Option to save changes to disk (if running locally)
if st.button("💾 Save Changes to TestData53684.csv (local only)"):
    edited_master.to_csv(MASTER_FILE, index=False)
    st.success("✅ Changes saved to TestData53684.csv")

# ==========================================================
# Trend Viewer
# ==========================================================
st.markdown("---")
st.header("📈 Trend Visualization")

# Detect columns by unit keywords
flow_cols = [c for c in edited_master.columns if "slpm" in str(c).lower()]
pressure_cols = [c for c in edited_master.columns if "bar" in str(c).lower()]
temp_cols = [c for c in edited_master.columns if any(x in str(c).lower() for x in ["°c", "temp", "centigrade"])]

# Sidebar toggles
st.sidebar.markdown("### Trend Options")
show_flow = st.sidebar.checkbox("Show Flow Trends (slpm)", True)
show_pressure = st.sidebar.checkbox("Show Pressure Trends (bar)", True)
show_temp = st.sidebar.checkbox("Show Temperature Trends (°C)", True)

# Pick time/index column
time_col = st.selectbox("🕒 Select Time or Index Column",
                        options=["(Index)"] + list(edited_master.columns))
if time_col == "(Index)":
    edited_master["Index"] = edited_master.index
    time_col = "Index"

# Plot selected columns
if show_flow and flow_cols:
    st.subheader("💧 Flow Trends (slpm)")
    selected = st.multiselect("Select Flow Columns", flow_cols, default=flow_cols[:1])
    if selected:
        st.line_chart(edited_master.set_index(time_col)[selected])

if show_pressure and pressure_cols:
    st.subheader("🧱 Pressure Trends (bar)")
    selected = st.multiselect("Select Pressure Columns", pressure_cols, default=pressure_cols[:1])
    if selected:
        st.line_chart(edited_master.set_index(time_col)[selected])

if show_temp and temp_cols:
    st.subheader("🌡️ Temperature Trends (°C)")
    selected = st.multiselect("Select Temperature Columns", temp_cols, default=temp_cols[:1])
    if selected:
        st.line_chart(edited_master.set_index(time_col)[selected])
