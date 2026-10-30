# 💰 FairShift – Financial Reconciliation System

Import invoices and payments, review matching suggestions, and manage
payment allocations. Built with Python, Streamlit, SQLite, pandas and rapidfuzz.

## Run

```bash
pip install -r requirements.txt
streamlit run app.py
```

1. Open the app and use the **Create Account** tab to make your account.
2. Login, go to **Import Data** and press **Use Sample Data** (or upload your own CSV files).
3. Open **Matching Review** to confirm or reject suggestions.
4. Check **Balances**, then export from **Reports**.

## Pages

| Page | What you can do |
|---|---|
| Login | Login or create an account |
| Dashboard | Totals, charts, quick links, recent decisions |
| Import Data | Upload CSVs, load sample data, clear data |
| Matching Review | Filter suggestions, confirm all High Confidence, confirm / reject / choose another invoice |
| Balances | Invoice, payment and customer balances with filters |
| Allocation History | See every decision and undo one |
| Reports | Generate, preview and download 5 CSV reports |
| My Account | Profile and change password |

## CSV format

Invoices: `invoice_id, customer_name, amount, invoice_date`
Payments: `payment_id, description, amount, payment_date`

## How matching works

Each payment is scored against every invoice:
40% invoice reference found in description + 30% customer name similarity +
20% exact amount + 10% date closeness.

Status: **High Confidence** (85+, exact amount), **Needs Review** (60+),
**Amount Mismatch** (short payment or overpayment), **Ambiguous** (two invoices
score almost the same), **Possible Duplicate** (same description, amount and
date as another payment), **Unmatched**.

## Security notes

- Passwords are salted and hashed (PBKDF2-SHA256); plain passwords are never saved.
- 5 wrong passwords lock the account for 5 minutes.
- Anyone who can open the app can create an account. If you deploy it
  publicly, add an approval step first.
- You stay logged in until you press Logout or refresh the browser tab.

## Tests

```bash
python -m pytest
```
