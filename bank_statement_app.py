import streamlit as st
import pandas as pd
import re
from io import BytesIO

# ---------------- PAGE CONFIG ----------------
st.set_page_config(
    page_title="Bank Statement Party Normalisation Tool",
    layout="wide"
)

st.title("🏦 Bank Statement Party Normalisation Tool")
st.caption("Firm Standard v1.1 — Audit & GST Safe")

# ---------------- CONSTANTS ----------------
BANK_CODE_WORDS = [
    "UBIN","BARB","YBL","AXL","AXIS","ICICI","HDFC","SBI","PNB","BOB",
    "YES","IDFC","KOTAK","PAYTM","IMPS","UPI","NEFT","ATM","CHARGES"
]

# ---------------- FUNCTIONS ----------------
def extract_party_ultra_strict(text):
    if pd.isna(text):
        return "Unidentified – Review Required"

    t = str(text).upper()

    # Stop parsing at symbols
    for stop in ["@", "**"]:
        if stop in t:
            t = t.split(stop)[0]

    # Remove bank codes
    for w in BANK_CODE_WORDS:
        t = re.sub(rf"\b{w}\b", " ", t)

    # Keep alphabets only
    t = re.sub(r"[^A-Z\s]", " ", t)
    t = re.sub(r"\s+", " ", t).strip()

    words = t.split()
    if len(words) < 2:
        return "Unidentified – Review Required"

    return " ".join(words[:3]).title()


def process_file(uploaded_file):
    df = pd.read_excel(uploaded_file)

    # Flexible column mapping
    col_map = {}
    for c in df.columns:
        cl = str(c).lower()
        if "date" in cl:
            col_map[c] = "Date"
        elif "desc" in cl or "particular" in cl:
            col_map[c] = "Narration"
        elif "withdraw" in cl or "dr" in cl:
            col_map[c] = "Debit"
        elif "deposit" in cl or "cr" in cl:
            col_map[c] = "Credit"

    df = df.rename(columns=col_map)

    df["Date"] = pd.to_datetime(df["Date"], errors="coerce").dt.date
    df["Party Name"] = df["Narration"].apply(extract_party_ultra_strict)
    df["Amount"] = pd.to_numeric(
        df.get("Credit").fillna(df.get("Debit")),
        errors="coerce"
    )

    return df[["Date", "Party Name", "Amount"]]


def generate_excel(cleaned_df, summary_df, unidentified_df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        cleaned_df.to_excel(writer, sheet_name="Cleaned_Transactions", index=False)
        summary_df.to_excel(writer, sheet_name="Party_Summary", index=False)
        unidentified_df.to_excel(writer, sheet_name="Unidentified_Review", index=False)
    return output.getvalue()

# ---------------- UI ----------------
uploaded_files = st.file_uploader(
    "Upload Bank Statement Excel Files (Multiple Allowed)",
    type=["xlsx"],
    accept_multiple_files=True
)

if uploaded_files:
    all_data = []

    for file in uploaded_files:
        processed = process_file(file)
        processed["Source File"] = file.name
        all_data.append(processed)

    combined_df = pd.concat(all_data, ignore_index=True)

    # Party summary
    summary_df = (
        combined_df.groupby("Party Name", as_index=False)["Amount"]
        .sum()
        .rename(columns={"Amount": "Total Amount"})
        .sort_values("Total Amount", key=abs, ascending=False)
    )

    unidentified_df = combined_df[
        combined_df["Party Name"] == "Unidentified – Review Required"
    ]

    # ----------- TABS -----------
    tab1, tab2, tab3 = st.tabs([
        "📄 Cleaned Transactions",
        "📊 Party-wise Summary",
        "⚠️ Unidentified / Review Required"
    ])

    with tab1:
        st.dataframe(combined_df, use_container_width=True)

    with tab2:
        st.dataframe(summary_df, use_container_width=True)

    with tab3:
        st.dataframe(unidentified_df, use_container_width=True)

    # ----------- EXCEL DOWNLOAD -----------
    excel_data = generate_excel(combined_df, summary_df, unidentified_df)

    st.download_button(
        label="⬇️ Download Excel Report",
        data=excel_data,
        file_name="Bank_Statement_Analysis_v1.1.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
