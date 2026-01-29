# Bank Statement Web App

A web-based application to clean bank statement data, normalise party names, and generate audit- and GST-ready party-wise summaries.

---

## 🚀 Features

- Upload bank statement Excel files
- Clean and standardise transaction narrations
- Remove bank codes (UBIN, BARB, YBL, AXL, etc.)
- Normalise party names (human/business names only)
- Generate party-wise total summaries
- Download cleaned outputs
- Audit-safe and GST-friendly logic

---

## 🧠 Firm Standard Logic

- Bank name ≠ Party name  
- Channel / handle ≠ Party name  
- Party name is extracted **only from narration**
- Bank codes and identifiers are removed
- Ambiguous transactions are marked as:
  **Unidentified – Review Required**

---

## 🛠️ How to Use

1. Open the web app
2. Upload the bank statement Excel file
3. Review cleaned transactions
4. Download:
   - Cleaned transaction data
   - Party-wise summary

---

## 🔒 Compliance Notes

- No manual editing of data
- No assumptions beyond narration text
- Suitable for:
  - Accounting
  - GST reconciliation
  - Audit working papers

---

## 📌 Tech Stack

- Python
- Streamlit
- Pandas
- OpenPyXL
