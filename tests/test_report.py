
import os

from modules import report
from modules.report import export_all_reports

from tests.test_database import load_sample


def test_export_all_reports(db, tmp_path, monkeypatch):

    monkeypatch.setattr(report, "REPORT_DIR", str(tmp_path))

    load_sample(db)

    files = export_all_reports()

    assert set(files.keys()) == {
        "invoice_report",
        "payment_report",
        "matching_report",
        "allocation_report",
        "customer_report"
    }

    for file_path in files.values():
        assert os.path.exists(file_path)

    with open(files["invoice_report"]) as file:
        assert len(file.readlines()) == 251
