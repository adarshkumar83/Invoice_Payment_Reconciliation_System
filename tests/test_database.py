
from modules.csv_import import import_invoices
from modules.csv_import import import_payments
from modules.normalization import normalize_invoices
from modules.normalization import normalize_payments
from modules.matching import suggest_matches


def load_sample(db):

    invoices = normalize_invoices(import_invoices("data/sample_invoices.csv"))
    payments = normalize_payments(import_payments("data/sample_payments.csv"))
    suggestions = suggest_matches(invoices, payments)

    db.save_invoices(invoices)
    db.save_payments(payments)
    db.save_suggestions(suggestions)


def test_save_and_read_records(db):

    load_sample(db)

    assert len(db.get_invoices()) == 250
    assert len(db.get_payments()) == 250
    assert len(db.get_suggestions()) == 250

    # Display values are saved, not the lowercase matching keys
    assert db.get_invoices().iloc[0]["invoice_id"] == "INV101"


def test_importing_twice_does_not_duplicate(db):

    load_sample(db)
    load_sample(db)

    assert len(db.get_invoices()) == 250


def test_clear_all_data_keeps_users(db):

    load_sample(db)

    db.save_user("adarsh", "Adarsh", "a@b.co", "hash")

    db.clear_all_data()

    assert len(db.get_invoices()) == 0
    assert db.count_users() == 1
