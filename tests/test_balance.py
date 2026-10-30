
import pytest

from decimal import Decimal

from modules.reconciliation import confirm_allocation
from modules.reconciliation import reject_suggestion
from modules.reconciliation import undo_decision
from modules.reconciliation import confirm_high_confidence
from modules.reconciliation import get_reconciliation_report
from modules.reconciliation import get_review_table
from modules.reconciliation import get_allocation_history
from modules.reconciliation import get_customer_summary

from tests.test_database import load_sample


def balance_of(invoice_id):

    invoices = get_reconciliation_report()["invoices"]

    return invoices[invoices["invoice_id"] == invoice_id].iloc[0]


def test_confirm_updates_balances(db):

    load_sample(db)

    confirm_allocation("PAY001", "INV101", "5000", "adarsh")

    invoice = balance_of("INV101")

    assert Decimal(invoice["paid_amount"]) == Decimal("5000")
    assert invoice["status"] == "Partially Paid"

    payments = get_reconciliation_report()["payments"]

    payment = payments[payments["payment_id"] == "PAY001"].iloc[0]

    assert payment["status"] == "Partially Allocated"
    assert Decimal(payment["unallocated_amount"]) == Decimal("7000")


def test_cannot_allocate_more_than_payment_or_invoice(db):

    load_sample(db)

    # PAY001 is 12000 for INV101 (12000)
    with pytest.raises(ValueError):
        confirm_allocation("PAY001", "INV101", "12000.01")

    with pytest.raises(ValueError):
        confirm_allocation("PAY001", "INV101", "0")

    with pytest.raises(ValueError):
        confirm_allocation("PAY001", "NOPE", "10")


def test_payment_cannot_be_allocated_twice(db):

    load_sample(db)

    confirm_allocation("PAY001", "INV101", "1000")

    with pytest.raises(ValueError):
        confirm_allocation("PAY001", "INV101", "1000")


def test_overpayment_leaves_unallocated_amount(db):

    load_sample(db)

    # PAY214 pays more than its invoice
    payments = db.get_payments()

    row = payments[payments["description"].str.contains("INV314")].iloc[0]

    confirm_allocation(row["payment_id"], "INV314", "3200")

    report = get_reconciliation_report()["payments"]

    payment = report[report["payment_id"] == row["payment_id"]].iloc[0]

    assert Decimal(payment["unallocated_amount"]) > 0
    assert balance_of("INV314")["status"] == "Paid"


def test_reject_and_undo(db):

    load_sample(db)

    reject_suggestion("PAY001", "INV101", "adarsh")

    review = get_review_table()

    assert review[review["payment_id"] == "PAY001"].iloc[0]["decision"] == "rejected"

    # A rejected payment can still be confirmed later
    confirm_allocation("PAY001", "INV101", "12000", "adarsh")

    with pytest.raises(ValueError):
        reject_suggestion("PAY001", "INV101")

    undo_decision("PAY001")

    review = get_review_table()

    assert review[review["payment_id"] == "PAY001"].iloc[0]["decision"] == "pending"
    assert balance_of("INV101")["status"] == "Unpaid"


def test_confirm_all_high_confidence(db):

    load_sample(db)

    confirmed, problems = confirm_high_confidence("adarsh")

    assert confirmed == 175
    assert problems == []

    # Running it again does nothing
    assert confirm_high_confidence("adarsh")[0] == 0

    history = get_allocation_history()

    assert len(history) == 175
    assert (history["decided_by"] == "adarsh").all()

    invoices = get_reconciliation_report()["invoices"]

    assert len(invoices[invoices["status"] == "Paid"]) == 175


def test_customer_summary(db):

    load_sample(db)

    summary = get_customer_summary()

    assert len(summary) == 20
    assert summary["invoices"].sum() == 250
