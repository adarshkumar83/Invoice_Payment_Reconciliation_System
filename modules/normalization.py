
import re
import pandas as pd

from decimal import Decimal, InvalidOperation


# Normalize text (used only for matching)
def normalize_text(text):

    if pd.isna(text):
        return ""

    # Convert text into lowercase
    text = str(text).lower()

    # Remove special characters
    text = re.sub(r"[^a-z0-9\s]", " ", text)

    # Remove extra spaces
    text = " ".join(text.split())

    return text


# Clean text for display (keeps capital letters)
def clean_text(text):

    if pd.isna(text):
        return ""

    return " ".join(str(text).split())


# Convert an amount into a fixed 2 decimal text, e.g. 3450.0 -> 3450.00
def format_amount(amount):

    try:
        value = Decimal(str(amount).replace(",", "").strip())
    except InvalidOperation:
        return str(amount)

    return str(value.quantize(Decimal("0.01")))


# Convert a date into YYYY-MM-DD
def format_date(date):

    converted = pd.to_datetime(date, errors="coerce")

    if pd.isna(converted):
        return str(date)

    return converted.strftime("%Y-%m-%d")


# Normalize invoice records
def normalize_invoices(invoices):

    invoices = invoices.copy()

    # Values that are saved and shown to the user
    invoices["invoice_id"] = invoices["invoice_id"].apply(
        lambda value: clean_text(value).upper()
    )

    invoices["customer_name"] = invoices["customer_name"].apply(
        clean_text
    )

    invoices["amount"] = invoices["amount"].apply(format_amount)

    invoices["invoice_date"] = invoices["invoice_date"].apply(
        format_date
    )

    # Clean values used for matching
    invoices["invoice_key"] = invoices["invoice_id"].apply(
        normalize_text
    )

    invoices["customer_key"] = invoices["customer_name"].apply(
        normalize_text
    )

    return invoices


# Normalize payment records
def normalize_payments(payments):

    payments = payments.copy()

    # Values that are saved and shown to the user
    payments["payment_id"] = payments["payment_id"].apply(
        lambda value: clean_text(value).upper()
    )

    payments["description"] = payments["description"].apply(
        clean_text
    )

    payments["amount"] = payments["amount"].apply(format_amount)

    payments["payment_date"] = payments["payment_date"].apply(
        format_date
    )

    # Clean value used for matching
    payments["description_key"] = payments["description"].apply(
        normalize_text
    )

    return payments
