
import streamlit as st

from modules.reconciliation import get_reconciliation_report
from modules.reconciliation import get_customer_summary

from modules.ui import require_login
from modules.ui import to_numbers
from modules.ui import money


require_login()

st.title("⚖️ Balances")

st.write("See what each customer still owes and which payments are not fully used.")

report = get_reconciliation_report()

if report["invoices"].empty:

    st.info("No records yet. Import your CSV files first.")

    st.page_link(
        "pages/import_data.py",
        label="Go to Import Data",
        icon="📥"
    )

    st.stop()

invoices = to_numbers(
    report["invoices"],
    ["invoice_amount", "paid_amount", "outstanding_amount"]
)

payments = to_numbers(
    report["payments"],
    ["payment_amount", "allocated_amount", "unallocated_amount"]
)

money_format = st.column_config.NumberColumn(format="₹%.2f")

invoice_tab, payment_tab, customer_tab = st.tabs(
    ["Invoice Balances", "Payment Balances", "Customer Summary"]
)


# Invoice balances
with invoice_tab:

    col1, col2, col3 = st.columns(3)

    col1.metric("Total Invoiced", money(invoices["invoice_amount"].sum()))

    col2.metric("Total Paid", money(invoices["paid_amount"].sum()))

    col3.metric(
        "Total Outstanding",
        money(invoices["outstanding_amount"].sum())
    )

    filter1, filter2 = st.columns(2)

    with filter1:

        invoice_status = st.multiselect(
            "Invoice status",
            ["Paid", "Partially Paid", "Unpaid"],
            default=["Partially Paid", "Unpaid"]
        )

    with filter2:

        invoice_search = st.text_input("Search invoice or customer")

    shown = invoices[invoices["status"].isin(invoice_status)]

    if invoice_search.strip() != "":

        text = invoice_search.strip().lower()

        shown = shown[
            shown["invoice_id"].str.lower().str.contains(text)
            | shown["customer_name"].str.lower().str.contains(text)
        ]

    st.caption(str(len(shown)) + " invoices shown")

    st.dataframe(
        shown,
        width="stretch",
        hide_index=True,
        column_config={
            "invoice_amount": money_format,
            "paid_amount": money_format,
            "outstanding_amount": money_format
        }
    )


# Payment balances
with payment_tab:

    col1, col2, col3 = st.columns(3)

    col1.metric("Total Received", money(payments["payment_amount"].sum()))

    col2.metric("Total Allocated", money(payments["allocated_amount"].sum()))

    col3.metric(
        "Total Unallocated",
        money(payments["unallocated_amount"].sum())
    )

    filter1, filter2 = st.columns(2)

    with filter1:

        payment_status = st.multiselect(
            "Payment status",
            ["Fully Allocated", "Partially Allocated", "Unallocated"],
            default=["Partially Allocated", "Unallocated"]
        )

    with filter2:

        payment_search = st.text_input("Search payment")

    shown = payments[payments["status"].isin(payment_status)]

    if payment_search.strip() != "":

        text = payment_search.strip().lower()

        shown = shown[
            shown["payment_id"].str.lower().str.contains(text)
            | shown["description"].str.lower().str.contains(text)
        ]

    st.caption(str(len(shown)) + " payments shown")

    st.dataframe(
        shown,
        width="stretch",
        hide_index=True,
        column_config={
            "payment_amount": money_format,
            "allocated_amount": money_format,
            "unallocated_amount": money_format
        }
    )


# Customer summary
with customer_tab:

    summary = get_customer_summary()

    st.dataframe(
        summary,
        width="stretch",
        hide_index=True,
        column_config={
            "total_invoiced": money_format,
            "total_paid": money_format,
            "total_outstanding": money_format
        }
    )

    st.bar_chart(
        summary.set_index("customer_name")["total_outstanding"]
    )
