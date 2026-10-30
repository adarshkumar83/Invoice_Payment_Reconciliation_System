
import streamlit as st

from modules.reconciliation import confirm_allocation
from modules.reconciliation import reject_suggestion
from modules.reconciliation import undo_decision
from modules.reconciliation import confirm_high_confidence
from modules.reconciliation import get_review_table
from modules.reconciliation import get_reconciliation_report

from modules.ui import current_user
from modules.ui import require_login
from modules.ui import show_message
from modules.ui import set_message
from modules.ui import to_numbers
from modules.ui import money


require_login()

username = current_user()["username"]

st.title("🔍 Matching Review")

st.write(
    "Check each payment, confirm the right invoice, or reject the "
    "suggestion. Nothing is allocated until you confirm it."
)

show_message()


review = get_review_table()

if review.empty:

    st.info("No matching suggestions yet. Import your CSV files first.")

    st.page_link(
        "pages/import_data.py",
        label="Go to Import Data",
        icon="📥"
    )

    st.stop()

review = to_numbers(
    review,
    ["payment_amount", "invoice_amount", "confidence"]
)

report = get_reconciliation_report()

invoice_balances = to_numbers(
    report["invoices"],
    ["invoice_amount", "paid_amount", "outstanding_amount"]
)

payment_balances = to_numbers(
    report["payments"],
    ["payment_amount", "allocated_amount", "unallocated_amount"]
)


# Summary
pending = review[review["decision"] == "pending"]

col1, col2, col3, col4 = st.columns(4)

col1.metric("Pending", len(pending))

col2.metric(
    "Confirmed",
    len(review[review["decision"] == "confirmed"])
)

col3.metric(
    "Rejected",
    len(review[review["decision"] == "rejected"])
)

col4.metric(
    "High Confidence Pending",
    len(pending[pending["status"] == "High Confidence"])
)

st.divider()


# Confirm all safe matches together
st.header("1. Quick Confirm")

high_count = len(pending[pending["status"] == "High Confidence"])

st.write(
    "High Confidence suggestions have the invoice reference, a similar "
    "customer name and the exact amount."
)

if st.button(
    "Confirm All High Confidence (" + str(high_count) + ")",
    disabled=high_count == 0
):

    confirmed, problems = confirm_high_confidence(username)

    if len(problems) > 0:
        set_message(
            "warning",
            str(confirmed) + " confirmed. Problems: " + "; ".join(problems)
        )
    else:
        set_message("success", str(confirmed) + " payments confirmed.")

    st.rerun()

st.divider()


# Suggestions table with filters
st.header("2. Matching Suggestions")

filter1, filter2, filter3 = st.columns(3)

with filter1:

    status_options = sorted(review["status"].unique())

    selected_status = st.multiselect(
        "Suggestion status",
        status_options,
        default=status_options
    )

with filter2:

    selected_decision = st.selectbox(
        "Decision",
        ["pending", "confirmed", "rejected", "all"]
    )

with filter3:

    search = st.text_input("Search payment or customer")

filtered = review[review["status"].isin(selected_status)]

if selected_decision != "all":
    filtered = filtered[filtered["decision"] == selected_decision]

if search.strip() != "":

    text = search.strip().lower()

    match = (
        filtered["payment_id"].str.lower().str.contains(text, na=False)
        | filtered["description"].str.lower().str.contains(text, na=False)
        | filtered["invoice_id"].str.lower().str.contains(text, na=False)
        | filtered["customer_name"].str.lower().str.contains(text, na=False)
    )

    filtered = filtered[match]

st.caption(str(len(filtered)) + " suggestions shown")

st.dataframe(
    filtered,
    width="stretch",
    hide_index=True,
    column_config={
        "payment_amount": st.column_config.NumberColumn(format="₹%.2f"),
        "invoice_amount": st.column_config.NumberColumn(format="₹%.2f"),
        "confidence": st.column_config.ProgressColumn(
            min_value=0,
            max_value=100,
            format="%.1f"
        )
    }
)

st.divider()


# Review one payment
st.header("3. Review a Payment")

if filtered.empty:

    st.info("No payments match the current filters.")

    st.stop()

payment_ids = filtered["payment_id"].tolist()

labels = {}

for index, row in filtered.iterrows():

    labels[row["payment_id"]] = (
        row["payment_id"]
        + "  |  "
        + row["description"]
        + "  |  "
        + money(row["payment_amount"])
    )

selected_payment = st.selectbox(
    "Select Payment",
    payment_ids,
    format_func=lambda payment_id: labels[payment_id]
)

selected_row = filtered[
    filtered["payment_id"] == selected_payment
].iloc[0]

payment_row = payment_balances[
    payment_balances["payment_id"] == selected_payment
].iloc[0]

suggested_invoice = selected_row["invoice_id"]

has_suggestion = isinstance(suggested_invoice, str)

detail1, detail2 = st.columns(2)

with detail1:

    st.subheader("Payment")

    st.write("**ID:**", selected_row["payment_id"])

    st.write("**Description:**", selected_row["description"])

    st.write("**Amount:**", money(selected_row["payment_amount"]))

    st.write("**Date:**", selected_row["payment_date"])

    st.write("**Unallocated:**", money(payment_row["unallocated_amount"]))

with detail2:

    st.subheader("Suggested Invoice")

    if has_suggestion:

        invoice_row = invoice_balances[
            invoice_balances["invoice_id"] == suggested_invoice
        ].iloc[0]

        st.write("**Invoice:**", suggested_invoice)

        st.write("**Customer:**", selected_row["customer_name"])

        st.write("**Invoice amount:**", money(selected_row["invoice_amount"]))

        st.write(
            "**Outstanding:**",
            money(invoice_row["outstanding_amount"])
        )

    else:

        st.write("No invoice was suggested for this payment.")

st.write("**Confidence:**", str(selected_row["confidence"]) + "%")

st.write("**Status:**", selected_row["status"])

st.write("**Explanation:**", selected_row["explanation"])

st.write("**Decision:**", selected_row["decision"])


# Already confirmed payments can only be undone
if selected_row["decision"] == "confirmed":

    st.info("This payment is already allocated.")

    if st.button("Undo This Allocation"):

        set_message("success", undo_decision(selected_payment))

        st.rerun()

    st.stop()


# Choose the invoice to allocate
choices = []

if has_suggestion:
    choices.append("Suggested invoice (" + suggested_invoice + ")")

choices.append("Choose another invoice")

choice = st.radio("Invoice to allocate", choices)

if choice == "Choose another invoice":

    open_invoices = invoice_balances[
        invoice_balances["outstanding_amount"] > 0
    ]

    open_labels = {}

    for index, row in open_invoices.iterrows():

        open_labels[row["invoice_id"]] = (
            row["invoice_id"]
            + "  |  "
            + row["customer_name"]
            + "  |  outstanding "
            + money(row["outstanding_amount"])
        )

    if open_invoices.empty:

        st.warning("There are no invoices with an outstanding amount.")

        st.stop()

    chosen_invoice = st.selectbox(
        "Invoice",
        open_invoices["invoice_id"].tolist(),
        format_func=lambda invoice_id: open_labels[invoice_id]
    )

else:

    chosen_invoice = suggested_invoice

chosen_row = invoice_balances[
    invoice_balances["invoice_id"] == chosen_invoice
].iloc[0]

max_amount = min(
    float(payment_row["unallocated_amount"]),
    float(chosen_row["outstanding_amount"])
)

if max_amount <= 0:

    st.warning(
        "Invoice " + chosen_invoice + " is already fully paid, "
        "so nothing more can be allocated to it."
    )

    allocation_amount = 0

else:

    allocation_amount = st.number_input(
        "Allocation Amount",
        min_value=0.01,
        max_value=max_amount,
        value=max_amount,
        step=100.0,
        format="%.2f"
    )

    st.caption(
        "Maximum: " + money(max_amount)
        + " (the smaller of the payment and the invoice outstanding)"
    )

button1, button2 = st.columns(2)

with button1:

    if st.button("Confirm Allocation", type="primary", disabled=max_amount <= 0):

        try:

            result = confirm_allocation(
                selected_payment,
                chosen_invoice,
                f"{allocation_amount:.2f}",
                username
            )

            set_message("success", result)

            st.rerun()

        except Exception as error:

            st.error(str(error))

with button2:

    if st.button("Reject Suggestion", disabled=not has_suggestion):

        try:

            result = reject_suggestion(
                selected_payment,
                suggested_invoice,
                username
            )

            set_message("warning", result)

            st.rerun()

        except Exception as error:

            st.error(str(error))
