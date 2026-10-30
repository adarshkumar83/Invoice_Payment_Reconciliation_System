
import pandas as pd

from modules.csv_import import import_invoices
from modules.csv_import import import_payments
from modules.normalization import normalize_invoices
from modules.normalization import normalize_payments
from modules.matching import suggest_matches
from modules.matching import calculate_name_similarity


def make_data(invoices, payments):

    invoices = normalize_invoices(pd.DataFrame(
        invoices,
        columns=["invoice_id", "customer_name", "amount", "invoice_date"]
    ))

    payments = normalize_payments(pd.DataFrame(
        payments,
        columns=["payment_id", "description", "amount", "payment_date"]
    ))

    return invoices, payments


def test_name_similarity_handles_short_names():

    assert calculate_name_similarity("nisha das", "nisha d inv171") > 80
    assert calculate_name_similarity("nisha das", "rohit gupta inv104") < 50


def test_exact_payment_is_high_confidence():

    invoices, payments = make_data(
        [["INV1", "Rahul Verma", 1000, "2026-10-01"],
         ["INV2", "Amit Malhotra", 2000, "2026-10-01"]],
        [["PAY1", "Rahul Verma INV1", 1000, "2026-10-02"]]
    )

    result = suggest_matches(invoices, payments).iloc[0]

    assert result["invoice_id"] == "INV1"
    assert result["status"] == "High Confidence"


def test_short_payment_is_amount_mismatch():

    invoices, payments = make_data(
        [["INV1", "Rahul Verma", 1000, "2026-10-01"],
         ["INV2", "Amit Malhotra", 2000, "2026-10-01"]],
        [["PAY1", "Rahul V INV1", 600, "2026-10-02"]]
    )

    result = suggest_matches(invoices, payments).iloc[0]

    assert result["invoice_id"] == "INV1"
    assert result["status"] == "Amount Mismatch"
    assert "short payment of 400.00" in result["explanation"]


def test_payment_without_reference_is_not_high_confidence():

    invoices, payments = make_data(
        [["INV1", "Rahul Verma", 1000, "2026-10-01"],
         ["INV2", "Amit Malhotra", 1000, "2026-10-01"]],
        [["PAY1", "BANK TRANSFER REF 7845", 1000, "2026-10-02"]]
    )

    result = suggest_matches(invoices, payments).iloc[0]

    assert result["status"] in ("Ambiguous", "Unmatched")


def test_duplicate_payment_is_flagged():

    invoices, payments = make_data(
        [["INV1", "Rahul Verma", 1000, "2026-10-01"]],
        [["PAY1", "BANK TRANSFER REF 7845", 500, "2026-10-02"],
         ["PAY2", "BANK TRANSFER REF 7845", 500, "2026-10-02"]]
    )

    result = suggest_matches(invoices, payments)

    assert result.iloc[0]["status"] != "Possible Duplicate"
    assert result.iloc[1]["status"] == "Possible Duplicate"


def test_sample_files_every_reference_is_found():

    invoices = normalize_invoices(import_invoices("data/sample_invoices.csv"))
    payments = normalize_payments(import_payments("data/sample_payments.csv"))

    result = suggest_matches(invoices, payments)

    payments["reference"] = payments["description"].str.extract(
        r"(INV\d+)", expand=False
    )

    merged = result.merge(payments[["payment_id", "reference"]], on="payment_id")

    with_reference = merged[merged["reference"].notna()]

    assert len(with_reference) == 238
    assert (with_reference["invoice_id"] == with_reference["reference"]).all()
