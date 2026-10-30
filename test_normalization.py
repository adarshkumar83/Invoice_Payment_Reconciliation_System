
import pandas as pd

from modules.normalization import normalize_text
from modules.normalization import normalize_invoices
from modules.normalization import normalize_payments


def test_normalize_text():

    assert normalize_text("  Rahul-Verma, INV101!! ") == "rahul verma inv101"
    assert normalize_text(None) == ""


def test_normalize_invoices_keeps_display_values():

    invoices = pd.DataFrame({
        "invoice_id": [" inv101 "],
        "customer_name": ["Rahul   Verma"],
        "amount": [3450],
        "invoice_date": ["2026-10-05"]
    })

    result = normalize_invoices(invoices).iloc[0]

    assert result["invoice_id"] == "INV101"
    assert result["customer_name"] == "Rahul Verma"
    assert result["amount"] == "3450.00"
    assert result["customer_key"] == "rahul verma"
    assert result["invoice_key"] == "inv101"


def test_normalize_payments():

    payments = pd.DataFrame({
        "payment_id": ["pay001"],
        "description": ["TRANSFER Rahul Verma INV101"],
        "amount": ["1200.5"],
        "payment_date": ["10/05/2026"]
    })

    result = normalize_payments(payments).iloc[0]

    assert result["payment_id"] == "PAY001"
    assert result["amount"] == "1200.50"
    assert result["description_key"] == "transfer rahul verma inv101"
    assert result["payment_date"] == "2026-10-05"
