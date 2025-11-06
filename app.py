import streamlit as st
import pandas as pd
import os

# Streamlit page setup
st.set_page_config(page_title="Dry Gas CSV Tool", layout="wide")

# Sidebar navigation
page = st.sidebar.radio("📘 Navigation", ["Compare", "Trend View"])

MASTER_FILE = "TestData53684.csv"
if os.path.exists(MASTER_FILE):
    master_df = pd.read_csv(MASTER_FILE)
else:
    master_df = pd.DataFrame()

uploaded_master = st.sidebar.file_uploader("📂 Upload Master CSV", type=["csv"])
if uploaded_master is not None:
    master_df = pd.read_csv(uploaded_master)

if master_df.empty:
    st.warning("⚠️ No CSV loaded. Please upload or include TestData53684.csv.")
    st.stop()

# ==========================================================
# PAGE 1 — COMPARISON
# ==========================================================
if page == "Compare":
    st.title("💨 Dry Gas — CSV Comparison & Validation")

    uploaded_test = st.file_uploader("📂 Upload Test CSV to Compare", type=["csv"])

    st.subheader("🧾 Master CSV (Editable)")
    edited_master = st.data_editor(master_df, num_rows="dynamic", use_container_width=True)
    st.download_button("💾 Download Edited Master CSV",
                       edited_master.to_csv(index=False), "master_updated.csv")

    if uploaded_test is not None:
        test_df = pd.read_csv(uploaded_test)
        all_cols = sorted(list(set(edited_master.columns).union(test_df.columns)))
        edited_master = edited_master.reindex(columns=all_cols)
        test_df = test_df.reindex(columns=all_cols)

        diffs = []
        for i in range(max(len(edited_master), len(test_df))):
            for col in all_cols:
                val_master = edited_master[col].iloc[i] if i < len(edited_master) else None
                val_test = test_df[col].iloc[i] if i < len(test_df) else None
                if str(val_master) != str(val_test):
                    diffs.append({"Row": i + 1, "Column": col,
                                  "Master": val_master, "Test": val_test})

        if diffs:
            diff_df = pd.DataFrame(diffs)
            st.warning(f"⚠️ Found {len(diff_df)} differences")
            st.dataframe(diff_df, use_container_width=True)
            st.download_button("⬇️ Download Differences",
                               diff_df.to_csv(index=False), "differences.csv")
        else:
            st.success("✅ No differences found between Master and Test CSVs")

    st.subheader("🧪 Quick Validation Checks")
    issues = []
    for i, row in edited_master.iterrows():
        if "DriveTorque" in edited_master.columns and pd.notna(row["DriveTorque"]):
            try:
                val = float(row["DriveTorque"])
                if not (-1 <= val <= 1):
                    issues.append({"Row": i + 1, "Column": "DriveTorque",
                                   "Value": val, "Issue": "Out of range (-1 to 1)"})
            except Exception:
                issues.append({"Row": i + 1, "Column": "DriveTorque",
                               "Value": row["DriveTorque"], "Issue": "Non-numeric value"})

        if "DriveSpeed" in edited_master.columns and pd.notna(row["DriveSpeed"]):
            try:
                val = float(row["DriveSpeed"])
                if val < 0:
                    issues.append({"Row": i + 1, "Column": "DriveSpeed",
                                   "Value": val, "Issue": "Negative value"})
            except Exception:
                issues.append({"Row": i + 1, "Column": "DriveSpeed",
                               "Value": row["DriveSpeed"], "Issue": "Non-numeric value"})

    if issues:
        issue_df = pd.DataFrame(issues)
        st.error(f"🚨 Found {len(issue_df)} validation issues")
        st.dataframe(issue_df, use_container_width=True)
        st.download_button("⬇️ Download Validation Report",
                           issue_df.to_csv(index=False), "validation_report.csv")
    else:
        st.success("✅ All validation checks passed")

# ==========================================================
# PAGE 2 — TREND VIEW (built-in charts only)
# ==========================================================
elif page == "Trend View":
    st.title("📈 Dry Gas Trend Visualization")

    flow_cols = [c for c in master_df.columns if "slpm" in c.lower()]
    pressure_cols = [c for c in master_df.columns if "bar" in c.lower()]
    temp_cols = [c for c in master_df.columns if any(x in c.lower() for x in ["°c", "centigrade", "temp"])]

    st.sidebar.markdown("### Trend Display Options")
    show_flow = st.sidebar.checkbox("Show Flow Trends (slpm)", True)
    show_pressure = st.sidebar.checkbox("Show Pressure Trends (bar)", True)
    show_temp = st.sidebar.checkbox("Show Temperature Trends (°C)", True)

    time_col = st.selectbox("🕒 Select Time/Index Column",
                            options=["(Index)"] + list(master_df.columns))
    if time_col == "(Index)":
        master_df["Index"] = master_df.index
        time_col = "Index"

    if show_flow and flow_cols:
        st.subheader("💧 Flow Trends (slpm)")
        st.line_chart(master_df.set_index(time_col)[flow_cols])

    if show_pressure and pressure_cols:
        st.subheader("🧱 Pressure Trends (bar)")
        st.line_chart(master_df.set_index(time_col)[pressure_cols])

    if show_temp and temp_cols:
        st.subheader("🌡️ Temperature Trends (°C)")
        st.line_chart(master_df.set_index(time_col)[temp_cols])

    if not (show_flow or show_pressure or show_temp):
        st.info("👁️ Enable one or more trend types from the sidebar to visualize data.")
