import streamlit as st
import pandas as pd
import re
from io import BytesIO

st.set_page_config(page_title="Bank Statement Analyzer", layout="wide")
st.title("🏦 Bank Statement Analyzer – Accounting Intelligence v2.0")
st.caption("Transferor-wise | Audit & ITR Ready")

# ---------------- NOISE CLEANER ----------------
def clean_narration(text):
    if pd.isna(text):
        return ""

    t = str(text)

    # Remove long reference numbers
    t = re.sub(r"\b[A-Z0-9]{8,}\b", " ", t)

    # Remove long digit runs (except phone-UPI)
    t = re.sub(r"\b\d{12,}\b", " ", t)

    # Replace separators with space
    t = re.sub(r"[\/\-\*\#]", " ", t)

    # Normalize spaces
    t = re.sub(r"\s+", " ", t).strip()

    return t

# ---------------- UPI ID EXTRACTOR ----------------
def extract_upi_id(text):
    matches = re.findall(r"\b[\w\.\-]{2,}@[\w]{2,}\b", text, flags=re.IGNORECASE)
    return matches[0] if matches else None

# ---------------- CLASSIFICATION ----------------
def classify_transaction(narr):
    n = narr.upper()

    if any(x in n for x in ["AMC", "CHARGE", "CHG", "FEE"]):
        return "Bank Charges"

    if "INTEREST" in n or "INT " in n:
        return "Bank Interest"

    if "CASH DEP" in n or "CASH DEPOSIT" in n:
        return "Cash Deposit"

    if "CASH WDL" in n or "ATM WDL" in n:
        return "Cash Withdrawal"

    if any(x in n for x in ["UPI", "IMPS", "NEFT", "RTGS"]):
        return "Transfer"

    return "Unidentified"

# ---------------- PARTY IDENTIFICATION ----------------
def identify_party(original_narr):
    cleaned = clean_narration(original_narr)

    # UPI ID has highest priority
    upi = extract_upi_id(cleaned)
    if upi:
        return upi

    tx_type = classify_transaction(cleaned)

    if tx_type in ["Bank Charges", "Bank Interest"]:
        return tx_type

    if tx_type in ["Cash Deposit", "Cash Withdrawal"]:
        return tx_type

    # Try extracting human/entity words
    words = re.findall(r"[A-Za-z]{3,}", cleaned)
    if words:
        return " ".join(words[:3]).title()

    # Fallback – keep cleaned narration
    return cleaned if cleaned else "Unidentified – Review Required"

# ---------------- FILE PROCESSOR ----------------
def process_file(file):
    df = pd.read_excel(file)

    col_map = {}
    for c in df.columns:
        cl = c.lower()
        if "date" in cl:
            col_map[c] = "Date"
        elif any(x in cl for x in ["details", "narration", "particular"]):
            col_map[c] = "Narration"
        elif any(x in cl for x in ["debit", "withdraw", "dr"]):
            col_map[c] = "Debit"
        elif any(x in cl for x in ["credit", "deposit", "cr"]):
            col_map[c] = "Credit"

    df = df.rename(columns=col_map)

    df["Date"] = pd.to_datetime(df["Date"], errors="coerce").dt.date
    df["Original Narration"] = df["Narration"]
    df["Cleaned Narration"] = df["Narration"].apply(clean_narration)
    df["Transaction Type"] = df["Cleaned Narration"].apply(classify_transaction)
    df["Party / Transferor"] = df["Original Narration"].apply(identify_party)

    df["Amount"] = df.get("Credit").fillna(0) - df.get("Debit").fillna(0)

    return df[
        ["Date", "Party / Transferor", "Transaction Type", "Amount",
         "Original Narration", "Cleaned Narration"]
    ]

# ---------------- UI ----------------
files = st.file_uploader(
    "Upload Bank Statement Excel Files",
    type=["xlsx"],
    accept_multiple_files=True
)

if files:
    all_df = pd.concat([process_file(f) for f in files], ignore_index=True)

    summary = (
        all_df.groupby("Party / Transferor", as_index=False)["Amount"]
        .sum()
        .sort_values("Amount", key=abs, ascending=False)
    )

    unidentified = all_df[
        all_df["Party / Transferor"].str.contains("Unidentified", na=False)
    ]

    tab1, tab2, tab3 = st.tabs(
        ["📄 Transactions", "📊 Transferor Summary", "⚠️ Review Required"]
    )

    with tab1:
        st.dataframe(all_df, use_container_width=True)

    with tab2:
        st.dataframe(summary, use_container_width=True)

    with tab3:
        st.dataframe(unidentified, use_container_width=True)

    # Excel Download
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        all_df.to_excel(writer, sheet_name="Transactions", index=False)
        summary.to_excel(writer, sheet_name="Summary", index=False)
        unidentified.to_excel(writer, sheet_name="Review_Required", index=False)

    st.download_button(
        "⬇️ Download Excel (Accounting Ready)",
        data=output.getvalue(),
        file_name="Bank_Statement_Analysis_v2.0.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
