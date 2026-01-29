
import streamlit as st
import pandas as pd
import re

st.set_page_config(page_title="Bank Statement Party Normaliser", layout="wide")

st.title("🏦 Bank Statement Party Normalisation Tool")
st.caption("Firm Standard v1.0 – Audit & GST Safe")

BANK_CODE_WORDS = [
    "UBIN","BARB","YBL","AXL","AXIS","ICICI","HDFC","SBI","PNB","BOB",
    "YES","IDFC","KOTAK","PAYTM","IMPS","UPI","NEFT","ATM","CHARGES"
]

def extract_party_ultra_strict(text):
    if pd.isna(text):
        return "Unidentified – Review Required"
    t = str(text).upper()
    for stop in ["@", "**"]:
        if stop in t:
            t = t.split(stop)[0]
    for w in BANK_CODE_WORDS:
        t = re.sub(rf"\b{w}\b", " ", t)
    t = re.sub(r"[^A-Z\s]", " ", t)
    t = re.sub(r"\s+", " ", t).strip()
    words = t.split()
    if len(words) < 2:
        return "Unidentified – Review Required"
    return " ".join(words[:3]).title()

uploaded = st.file_uploader("Upload Bank Statement (Excel)", type=["xlsx"])

if uploaded:
    df = pd.read_excel(uploaded)

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
    df["Party Name (Final)"] = df["Narration"].apply(extract_party_ultra_strict)
    df["Amount"] = pd.to_numeric(df.get("Credit").fillna(df.get("Debit")), errors="coerce")

    cleaned = df[["Date","Party Name (Final)","Amount"]]

    summary = (
        cleaned.groupby("Party Name (Final)", as_index=False)["Amount"]
        .sum()
        .rename(columns={"Amount":"Total Amount"})
        .sort_values("Total Amount", key=abs, ascending=False)
    )

    st.subheader("📄 Cleaned Transactions")
    st.dataframe(cleaned, use_container_width=True)

    st.subheader("📊 Party-wise Summary")
    st.dataframe(summary, use_container_width=True)

    st.download_button(
        "⬇️ Download Cleaned Excel",
        data=cleaned.to_csv(index=False),
        file_name="cleaned_transactions.csv"
    )

    st.download_button(
        "⬇️ Download Party Summary",
        data=summary.to_csv(index=False),
        file_name="party_summary.csv"
    )
