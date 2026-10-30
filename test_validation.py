
import pandas as pd

from modules.validation import validate_invoices
from modules.validation import validate_payments
from modules.csv_import import import_invoices
from modules.csv_import import import_payments


def test_sample_files_are_valid():

    assert validate_invoices(import_invoices("data/sample_invoices.csv")) == []
    assert validate_payments(import_payments("data/sample_payments.csv")) == []


def test_missing_column():

    invoices = pd.DataFrame({"invoice_id": ["INV1"]})

    errors = validate_invoices(invoices)

    assert "Missing column: amount" in errors


def test_bad_values_are_reported():

    invoices = pd.DataFrame({
        "invoice_id": ["INV1", "INV1"],
        "customer_name": ["A", None],
        "amount": ["abc", "10"],
        "invoice_date": ["2026-10-01", "not a date"]
    })

    errors = validate_invoices(invoices)

    assert "Some customer names are missing" in errors
    assert "Some invoice amounts are invalid" in errors
    assert "Some invoice dates are invalid" in errors
    assert "Duplicate invoice IDs found" in errors


def test_negative_payment_amount():

    payments = pd.DataFrame({
        "payment_id": ["PAY1"],
        "description": ["test"],
        "amount": [-5],
        "payment_date": ["2026-10-01"]
    })

    assert "Payment amounts must be greater than zero" in validate_payments(payments)
