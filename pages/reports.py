
import os

import pandas as pd
import streamlit as st

from modules.report import export_all_reports

from modules.ui import require_login
from modules.ui import show_message
from modules.ui import set_message

from database.database import get_invoices


require_login()

st.title("📄 Reports")

st.write("Create CSV reports from the current balances and decisions.")

show_message()

if get_invoices().empty:

    st.info("No records yet. Import your CSV files first.")

    st.page_link(
        "pages/import_data.py",
        label="Go to Import Data",
        icon="📥"
    )

    st.stop()


report_names = {
    "invoice_report": "Invoice balances",
    "payment_report": "Payment balances",
    "matching_report": "Matching suggestions and decisions",
    "allocation_report": "Allocation history",
    "customer_report": "Customer summary"
}

if st.button("Generate CSV Reports", type="primary"):

    try:

        st.session_state["reports"] = export_all_reports()

        set_message("success", "Reports generated successfully!")

        st.rerun()

    except Exception as error:

        st.error("Report error: " + str(error))


reports = st.session_state.get("reports")

if reports is None:

    st.info("Click the button to create the latest reports.")

    st.stop()

st.subheader("Download")

for report_name, file_path in reports.items():

    with open(file_path, "rb") as file:

        file_data = file.read()

    left, right = st.columns([3, 1])

    with left:

        st.write("**" + report_names[report_name] + "**")

        st.caption(os.path.basename(file_path))

    with right:

        st.download_button(
            label="Download",
            data=file_data,
            file_name=os.path.basename(file_path),
            mime="text/csv",
            key=report_name,
            width="stretch"
        )

st.divider()

st.subheader("Preview")

selected_report = st.selectbox(
    "Report",
    list(reports.keys()),
    format_func=lambda name: report_names[name]
)

preview = pd.read_csv(reports[selected_report])

st.dataframe(preview, width="stretch", hide_index=True)
