
from modules.csv_import import import_invoices
from modules.csv_import import import_payments


def test_import_sample_files():

    invoices = import_invoices("data/sample_invoices.csv")
    payments = import_payments("data/sample_payments.csv")

    assert len(invoices) == 250
    assert len(payments) == 250

    assert list(invoices.columns) == [
        "invoice_id", "customer_name", "amount", "invoice_date"
    ]

    assert list(payments.columns) == [
        "payment_id", "description", "amount", "payment_date"
    ]
