
import os
import pandas as pd

from modules.reconciliation import get_reconciliation_report
from modules.reconciliation import get_review_table
from modules.reconciliation import get_allocation_history
from modules.reconciliation import get_customer_summary


# Get the reports folder
BASE_DIR = os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)

REPORT_DIR = os.path.join(BASE_DIR, "reports")


# Create reports folder if it does not exist
def create_report_folder():

    if not os.path.exists(REPORT_DIR):
        os.makedirs(REPORT_DIR)


# Export invoice balance report
def export_invoice_report():

    create_report_folder()

    report = get_reconciliation_report()

    invoice_data = report["invoices"]

    file_path = os.path.join(
        REPORT_DIR,
        "invoice_balances.csv"
    )

    invoice_data.to_csv(file_path, index=False)

    return file_path


# Export payment balance report
def export_payment_report():

    create_report_folder()

    report = get_reconciliation_report()

    payment_data = report["payments"]

    file_path = os.path.join(
        REPORT_DIR,
        "payment_balances.csv"
    )

    payment_data.to_csv(file_path, index=False)

    return file_path


# Export matching suggestions
def export_matching_report():

    create_report_folder()

    suggestions = get_review_table()

    file_path = os.path.join(
        REPORT_DIR,
        "matching_suggestions.csv"
    )

    suggestions.to_csv(file_path, index=False)

    return file_path


# Export confirmed and rejected decisions
def export_allocation_report():

    create_report_folder()

    history = get_allocation_history()

    file_path = os.path.join(
        REPORT_DIR,
        "allocations.csv"
    )

    history.to_csv(file_path, index=False)

    return file_path


# Export customer outstanding summary
def export_customer_report():

    create_report_folder()

    summary = get_customer_summary()

    file_path = os.path.join(
        REPORT_DIR,
        "customer_summary.csv"
    )

    summary.to_csv(file_path, index=False)

    return file_path


# Export all reconciliation reports
def export_all_reports():

    invoice_file = export_invoice_report()

    payment_file = export_payment_report()

    matching_file = export_matching_report()

    allocation_file = export_allocation_report()

    customer_file = export_customer_report()

    return {
        "invoice_report": invoice_file,
        "payment_report": payment_file,
        "matching_report": matching_file,
        "allocation_report": allocation_file,
        "customer_report": customer_file
    }
