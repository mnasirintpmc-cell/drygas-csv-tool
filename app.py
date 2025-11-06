# app.py
import streamlit as st
import pandas as pd
import os

st.set_page_config(page_title="Dry Gas CSV Tool", layout="wide")
st.title("💨 Dry Gas Testing — Master Editor, Comparator & Validator")

# ---------- Config ----------
DEFAULT_MASTER = "TestData53684.csv"  # if this file exists in the repo it will be loaded automatically

# ---------- Load default master if present ----------
master_df = None
if os.path.exists(DEFAULT_MASTER):
    try:
        master_df = pd.read_csv(DEFAULT_MASTER)
        st.sidebar.success(f"Loaded default master: {DEFAULT_MASTER}")
    except Exception as e:
        st.sidebar.error(f"Failed to load default master CSV: {e}")

# ---------- Upload controls ----------
st.sidebar.header("Data Controls")
uploaded_master = st.sidebar.file_uploader("Upload Master CSV (optional)", type=["csv"])
uploaded_test = st.sidebar.file_uploader("Upload Test CSV to compare", type=["csv"])

if uploaded_master is not None:
    try:
        master_df = pd.read_csv(uploaded_master)
        st.sidebar.success("Master CSV uploaded")
    except Exception as e:
        st.sidebar.error(f"Failed to parse uploaded master CSV: {e}")

# ---------- Show / edit master ----------
if master_df is not None:
    st.subheader("🧾 Master CSV (editable)")
    edited_master = st.data_editor(master_df, num_rows="dynamic", use_container_width=True, key="master_editor")
    # allow downloading the edited master
    st.download_button(
        "💾 Download Edited Master CSV",
        edited_master.to_csv(index=False).encode("utf-8"),
        "master_updated.csv",
        "text/csv",
    )
else:
    st.info("Upload a master CSV or include 'TestData53684.csv' in the repo to auto-load.")

st.markdown("---")

# ---------- Choose key column for matching ----------
if master_df is not None:
    cols = list(edited_master.columns)
    key_choice = st.selectbox("🔑 Select key column for row matching (choose Index to compare by position)", options=["(Index)"] + cols)
else:
    key_choice = "(Index)"

# ---------- Comparison ----------
if uploaded_test is not None:
    try:
        test_df = pd.read_csv(uploaded_test)
    except Exception as e:
        st.error(f"Failed to read test CSV: {e}")
        st.stop()

    st.subheader("🔍 Comparison Results")
    # align by key if available in both
    if key_choice != "(Index)" and key_choice in edited_master.columns and key_choice in test_df.columns:
        left = edited_master.set_index(key_choice)
        right = test_df.set_index(key_choice)
        st.info(f"Comparing by key column: {key_choice} (index-based comparison disabled)")
    else:
        left = edited_master.reset_index(drop=True)
        right = test_df.reset_index(drop=True)
        st.info("Comparing by row position (Index)")

    # union columns
    all_cols = list(pd.Index(left.columns).union(right.columns))
    left = left.reindex(columns=all_cols)
    right = right.reindex(columns=all_cols)

    # perform comparison
    diffs = []
    # iterate over union of indices
    all_index = list(pd.Index(left.index).union(right.index))
    for idx in all_index:
        for col in all_cols:
            a = left.at[idx, col] if col in left.columns and idx in left.index else pd.NA
            b = right.at[idx, col] if col in right.columns and idx in right.index else pd.NA
            # treat NaN == NaN
            if pd.isna(a) and pd.isna(b):
                continue
            if (pd.isna(a) and not pd.isna(b)) or (not pd.isna(a) and pd.isna(b)) or str(a) != str(b):
                diffs.append({"Key": idx, "Column": col, "Master": a, "Test": b})

    if not diffs:
        st.success("✅ No differences found between master and test CSVs!")
    else:
        diff_df = pd.DataFrame(diffs)
        st.warning(f"⚠️ Found {len(diff_df)} differences across {diff_df['Key'].nunique()} rows.")
        st.dataframe(diff_df, use_container_width=True)
        st.download_button(
            "⬇️ Download Diff Report",
            diff_df.to_csv(index=False).encode("utf-8"),
            "diff_report.csv",
            "text/csv",
        )

st.markdown("---")

# ---------- Validation rules ----------
st.subheader("🧪 Validation Checks (Master)")

validation_issues = []
if master_df is not None:
    # use the edited master for validation when present
    df_for_validation = edited_master.copy()
    for i, row in df_for_validation.iterrows():
        # Example rule: DriveTorque should be between -1.0 and 1.0 (customize as needed)
        if "DriveTorque" in df_for_validation.columns and pd.notna(row.get("DriveTorque")):
            try:
                val = float(row["DriveTorque"])
                if not (-1.0 <= val <= 1.0):
                    validation_issues.append({"Row": i, "Column": "DriveTorque", "Value": val, "Issue": "Torque out of expected range (-1 to 1)"})
            except Exception:
                validation_issues.append({"Row": i, "Column": "DriveTorque", "Value": row["DriveTorque"], "Issue": "Non-numeric DriveTorque"})
        # Example rule: DriveSpeed must be non-negative
        if "DriveSpeed" in df_for_validation.columns and pd.notna(row.get("DriveSpeed")):
            try:
                val = float(row["DriveSpeed"])
                if val < 0:
                    validation_issues.append({"Row": i, "Column": "DriveSpeed", "Value": val, "Issue": "Negative DriveSpeed"})
            except Exception:
                validation_issues.append({"Row": i, "Column": "DriveSpeed", "Value": row["DriveSpeed"], "Issue": "Non-numeric DriveSpeed"})
        # Generic rule: any column containing 'Flow' should be numeric and non-negative
        for col in df_for_validation.columns:
            if "Flow" in col and pd.notna(row.get(col)):
                try:
                    fv = float(row[col])
                    if fv < 0:
                        validation_issues.append({"Row": i, "Column": col, "Value": fv, "Issue": "Negative flow value"})
                except Exception:
                    validation_issues.append({"Row": i, "Column": col, "Value": row[col], "Issue": "Non-numeric flow value"})

    if validation_issues:
        val_df = pd.DataFrame(validation_issues)
        st.error(f"🚨 Found {len(val_df)} validation issues")
        st.dataframe(val_df, use_container_width=True)
        st.download_button(
            "⬇️ Download Validation Report",
            val_df.to_csv(index=False).encode("utf-8"),
            "validation_report.csv",
            "text/csv",
        )
    else:
        st.success("✅ No validation issues found in master data.")
else:
    st.info("Upload or provide a master CSV to run validation checks.")

st.markdown("---")
st.caption("Tip: customize the validation rules in app.py to match your lab acceptance criteria.")
