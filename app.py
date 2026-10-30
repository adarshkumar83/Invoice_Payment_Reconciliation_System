
import streamlit as st

from database.database import create_tables

from modules.ui import current_user
from modules.ui import logout_session


# Page configuration (only once, in the main file)
st.set_page_config(
    page_title="FairShift",
    page_icon="💰",
    layout="wide"
)


# Create database tables
create_tables()


user = current_user()


if user is None:

    # Visitors can only see the login page
    login_page = st.Page(
        "pages/login.py",
        title="Login",
        icon="🔐"
    )

    page = st.navigation([login_page], position="hidden")

else:

    # Pages for logged in users
    dashboard_page = st.Page(
        "pages/dashboard.py",
        title="Dashboard",
        icon="📊",
        default=True
    )

    import_page = st.Page(
        "pages/import_data.py",
        title="Import Data",
        icon="📥"
    )

    review_page = st.Page(
        "pages/matching_review.py",
        title="Matching Review",
        icon="🔍"
    )

    balances_page = st.Page(
        "pages/balances.py",
        title="Balances",
        icon="⚖️"
    )

    history_page = st.Page(
        "pages/allocation_history.py",
        title="Allocation History",
        icon="🧾"
    )

    reports_page = st.Page(
        "pages/reports.py",
        title="Reports",
        icon="📄"
    )

    account_page = st.Page(
        "pages/account.py",
        title="My Account",
        icon="👤"
    )

    page = st.navigation({
        "Overview": [dashboard_page],
        "Reconciliation": [import_page, review_page],
        "Records": [balances_page, history_page],
        "More": [reports_page, account_page]
    })

    # User box and logout button in the sidebar
    with st.sidebar:

        st.divider()

        st.write("👤 **" + user["full_name"] + "**")

        st.caption("@" + user["username"])

        if st.button("Logout", width="stretch"):

            logout_session()

            st.rerun()


page.run()
