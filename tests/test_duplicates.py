
import pandas as pd

from modules.normalization import normalize_payments
from modules.duplicates import find_duplicate_payments


def test_find_duplicates():

    payments = normalize_payments(pd.DataFrame({
        "payment_id": ["PAY1", "PAY2", "PAY3", "PAY4"],
        "description": ["Bank Transfer 1", "BANK TRANSFER 1", "Bank Transfer 1", "Other"],
        "amount": [100, 100, 150, 100],
        "payment_date": ["2026-10-01"] * 4
    }))

    assert find_duplicate_payments(payments) == {"PAY2": "PAY1"}


def test_no_duplicates():

    payments = normalize_payments(pd.DataFrame({
        "payment_id": ["PAY1", "PAY2"],
        "description": ["A INV1", "B INV2"],
        "amount": [100, 100],
        "payment_date": ["2026-10-01", "2026-10-01"]
    }))

    assert find_duplicate_payments(payments) == {}
