
import streamlit as st

from database.database import get_invoices
from database.database import get_payments

from modules.reconciliation import get_reconciliation_report
from modules.reconciliation import get_review_table
from modules.reconciliation import get_allocation_history

from modules.ui import current_user
from modules.ui import require_login
from modules.ui import show_message
from modules.ui import to_numbers
from modules.ui import money


require_login()

user = current_user()

st.title("📊 Dashboard")

st.write("Welcome back, **" + user["full_name"] + "**.")

show_message()

# Show an empty page message when there is no data
if len(get_invoices()) == 0 or len(get_payments()) == 0:

    st.info(
        "No records yet. Import your invoice and payment "
        "CSV files to get started."
    )

    st.page_link(
        "pages/import_data.py",
        label="Go to Import Data",
        icon="📥"
    )

    st.stop()


# Load the numbers
report = get_reconciliation_report()

invoices = to_numbers(
    report["invoices"],
    ["invoice_amount", "paid_amount", "outstanding_amount"]
)

payments = to_numbers(
    report["payments"],
    ["payment_amount", "allocated_amount", "unallocated_amount"]
)

review = get_review_table()

pending = review[review["decision"] == "pending"]

high_pending = pending[pending["status"] == "High Confidence"]


# Summary
col1, col2, col3, col4 = st.columns(4)

col1.metric("Total Invoices", len(invoices))

col2.metric("Total Payments", len(payments))

col3.metric(
    "Outstanding Amount",
    money(invoices["outstanding_amount"].sum())
)

col4.metric(
    "Unallocated Payments",
    money(payments["unallocated_amount"].sum())
)

col5, col6, col7, col8 = st.columns(4)

col5.metric(
    "Paid Invoices",
    len(invoices[invoices["status"] == "Paid"])
)

col6.metric(
    "Unpaid / Partial",
    len(invoices[invoices["status"] != "Paid"])
)

col7.metric("Payments To Review", len(pending))

col8.metric("High Confidence Pending", len(high_pending))

st.divider()


# Charts
chart_left, chart_right = st.columns(2)

with chart_left:

    st.subheader("Matching Suggestions")

    st.bar_chart(review["status"].value_counts())

with chart_right:

    st.subheader("Invoice Status")

    st.bar_chart(invoices["status"].value_counts())

st.divider()


# Quick links
st.subheader("Quick Actions")

link1, link2, link3, link4 = st.columns(4)

with link1:
    st.page_link("pages/import_data.py", label="Import Data", icon="📥")

with link2:
    st.page_link("pages/matching_review.py", label="Review Matches", icon="🔍")

with link3:
    st.page_link("pages/balances.py", label="View Balances", icon="⚖️")

with link4:
    st.page_link("pages/reports.py", label="Export Reports", icon="📄")

st.divider()


# Recent decisions
st.subheader("Recent Decisions")

history = get_allocation_history()

if history.empty:

    st.info("No decisions saved yet.")

else:

    st.dataframe(
        history.head(5)[
            [
                "payment_id",
                "invoice_id",
                "customer_name",
                "allocated_amount",
                "status",
                "decided_by",
                "decision_date"
            ]
        ],
        width="stretch",
        hide_index=True
    )

    st.page_link(
        "pages/allocation_history.py",
        label="See all decisions",
        icon="🧾"
    )
