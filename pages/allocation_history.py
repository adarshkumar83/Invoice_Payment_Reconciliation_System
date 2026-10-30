
import streamlit as st

from modules.reconciliation import get_allocation_history
from modules.reconciliation import undo_decision

from modules.ui import require_login
from modules.ui import show_message
from modules.ui import set_message
from modules.ui import to_numbers
from modules.ui import money


require_login()

st.title("🧾 Allocation History")

st.write("Every confirmed or rejected decision, with who made it and when.")

show_message()

history = get_allocation_history()

if history.empty:

    st.info("No decisions have been saved yet.")

    st.page_link(
        "pages/matching_review.py",
        label="Go to Matching Review",
        icon="🔍"
    )

    st.stop()

history = to_numbers(history, ["allocated_amount"])


# Summary
confirmed = history[history["status"] == "confirmed"]

col1, col2, col3 = st.columns(3)

col1.metric("Confirmed", len(confirmed))

col2.metric("Rejected", len(history[history["status"] == "rejected"]))

col3.metric("Total Allocated", money(confirmed["allocated_amount"].sum()))

st.divider()


# Filters
filter1, filter2 = st.columns(2)

with filter1:

    selected_status = st.selectbox(
        "Decision",
        ["all", "confirmed", "rejected"]
    )

with filter2:

    search = st.text_input("Search payment, invoice, customer or user")

shown = history

if selected_status != "all":
    shown = shown[shown["status"] == selected_status]

if search.strip() != "":

    text = search.strip().lower()

    shown = shown[
        shown["payment_id"].str.lower().str.contains(text)
        | shown["invoice_id"].str.lower().str.contains(text)
        | shown["customer_name"].str.lower().str.contains(text)
        | shown["decided_by"].fillna("").str.lower().str.contains(text)
    ]

st.caption(str(len(shown)) + " decisions shown")

st.dataframe(
    shown,
    width="stretch",
    hide_index=True,
    column_config={
        "allocated_amount": st.column_config.NumberColumn(format="₹%.2f")
    }
)

st.divider()


# Undo a decision
st.header("Undo a Decision")

st.write(
    "Removing a decision puts the payment back in the review list "
    "and the invoice balance is recalculated."
)

if shown.empty:

    st.info("No decisions to undo with the current filters.")

    st.stop()

labels = {}

for index, row in shown.iterrows():

    labels[row["payment_id"]] = (
        row["payment_id"]
        + " -> "
        + row["invoice_id"]
        + "  |  "
        + row["status"]
        + "  |  "
        + money(row["allocated_amount"])
    )

undo_payment = st.selectbox(
    "Decision",
    shown["payment_id"].tolist(),
    format_func=lambda payment_id: labels[payment_id]
)

if st.button("Undo Selected Decision"):

    set_message("success", undo_decision(undo_payment))

    st.rerun()
