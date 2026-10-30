
import os

import streamlit as st

from database.database import BASE_DIR
from database.database import get_invoices
from database.database import get_payments
from database.database import save_invoices
from database.database import save_payments
from database.database import save_suggestions
from database.database import clear_all_data

from modules.csv_import import import_invoices
from modules.csv_import import import_payments

from modules.validation import validate_invoices
from modules.validation import validate_payments

from modules.normalization import normalize_invoices
from modules.normalization import normalize_payments

from modules.matching import suggest_matches

from modules.ui import require_login
from modules.ui import show_message
from modules.ui import set_message


require_login()


# Read, check, clean, match and save the two files
def process_files(invoice_source, payment_source):

    try:

        # Import CSV files
        invoices_data = import_invoices(invoice_source)

        payments_data = import_payments(payment_source)

    except Exception as error:

        st.error("Could not read the CSV files: " + str(error))

        return

    # Validate records
    invoice_errors = validate_invoices(invoices_data)

    payment_errors = validate_payments(payments_data)

    if invoice_errors or payment_errors:

        for error in invoice_errors:
            st.error("Invoice: " + error)

        for error in payment_errors:
            st.error("Payment: " + error)

        return

    try:

        # Normalize records
        invoices_data = normalize_invoices(invoices_data)

        payments_data = normalize_payments(payments_data)

        # Generate matching suggestions
        suggestions_data = suggest_matches(
            invoices_data,
            payments_data
        )

        # Save records in database
        save_invoices(invoices_data)

        save_payments(payments_data)

        save_suggestions(suggestions_data)

    except Exception as error:

        st.error("Error processing files: " + str(error))

        return

    st.session_state["import_summary"] = {
        "invoices": len(invoices_data),
        "payments": len(payments_data),
        "status_counts": suggestions_data["status"].value_counts().to_dict()
    }

    set_message("success", "CSV files processed successfully!")

    st.rerun()


st.title("📥 Import Data")

st.write(
    "Upload an invoice file and a payment file. FairShift checks the "
    "records and prepares matching suggestions for you to review."
)

show_message()


# Show the result of the last import
summary = st.session_state.get("import_summary")

if summary is not None:

    st.subheader("Last Import")

    col1, col2 = st.columns(2)

    col1.metric("Invoices imported", summary["invoices"])

    col2.metric("Payments imported", summary["payments"])

    st.write("Suggestions created:")

    status_columns = st.columns(max(len(summary["status_counts"]), 1))

    index = 0

    for status, count in summary["status_counts"].items():

        status_columns[index].metric(status, count)

        index += 1

    st.page_link(
        "pages/matching_review.py",
        label="Continue to Matching Review",
        icon="🔍"
    )

    st.divider()


# Upload section
st.header("1. Upload CSV Files")

with st.expander("Required columns"):

    st.write("**Invoice file:** invoice_id, customer_name, amount, invoice_date")

    st.write("**Payment file:** payment_id, description, amount, payment_date")

    st.write("Dates should look like 2026-10-25.")

col1, col2 = st.columns(2)

with col1:

    invoice_file = st.file_uploader(
        "Upload Invoice CSV",
        type=["csv"],
        key="invoice_upload"
    )

with col2:

    payment_file = st.file_uploader(
        "Upload Payment CSV",
        type=["csv"],
        key="payment_upload"
    )

button1, button2 = st.columns(2)

with button1:

    if st.button("Process CSV Files", type="primary", width="stretch"):

        if invoice_file is None or payment_file is None:

            st.error("Please upload both CSV files.")

        else:

            process_files(invoice_file, payment_file)

with button2:

    if st.button("Use Sample Data (250 records)", width="stretch"):

        process_files(
            os.path.join(BASE_DIR, "data", "sample_invoices.csv"),
            os.path.join(BASE_DIR, "data", "sample_payments.csv")
        )

st.divider()


# Current database records
st.header("2. Saved Records")

saved_invoices = get_invoices()

saved_payments = get_payments()

col1, col2 = st.columns(2)

col1.metric("Invoices in database", len(saved_invoices))

col2.metric("Payments in database", len(saved_payments))

st.caption(
    "Importing a file with an existing invoice or payment ID "
    "updates that record. Your saved decisions are kept."
)

st.divider()


# Delete everything
st.header("3. Clear Data")

with st.expander("Delete all invoices, payments and decisions"):

    st.warning(
        "This deletes every invoice, payment, suggestion and "
        "allocation. User accounts are not deleted."
    )

    sure = st.checkbox("I understand that this cannot be undone")

    if st.button("Delete All Data", disabled=not sure):

        clear_all_data()

        st.session_state.pop("import_summary", None)

        set_message("success", "All records were deleted.")

        st.rerun()
