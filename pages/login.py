
import streamlit as st

from modules.auth import authenticate
from modules.auth import register_user
from modules.ui import login_session

from database.database import count_users


st.title("💰 FairShift")

st.subheader("Financial Reconciliation System")

st.write(
    "Import invoices and payments, review matching suggestions, "
    "and manage payment allocations."
)

st.divider()

if count_users() == 0:
    st.info("No accounts yet. Create the first account in the next tab.")

left, middle, right = st.columns([1, 2, 1])

with middle:

    login_tab, register_tab = st.tabs(["Login", "Create Account"])

    # Login form
    with login_tab:

        with st.form("login_form"):

            username = st.text_input("Username")

            password = st.text_input("Password", type="password")

            login_clicked = st.form_submit_button(
                "Login",
                type="primary",
                width="stretch"
            )

        if login_clicked:

            if username.strip() == "" or password == "":

                st.error("Please enter username and password.")

            else:

                user, error = authenticate(username, password)

                if user is None:

                    st.error(error)

                else:

                    login_session(user)

                    st.rerun()

    # Registration form
    with register_tab:

        with st.form("register_form"):

            full_name = st.text_input("Full name")

            new_username = st.text_input(
                "Username",
                help="3-30 letters, numbers or underscore",
                key="register_username"
            )

            email = st.text_input("Email")

            new_password = st.text_input(
                "Password",
                type="password",
                help="At least 8 characters with a letter and a number",
                key="register_password"
            )

            confirm_password = st.text_input(
                "Confirm password",
                type="password"
            )

            register_clicked = st.form_submit_button(
                "Create Account",
                type="primary",
                width="stretch"
            )

        if register_clicked:

            errors = register_user(
                new_username,
                full_name,
                email,
                new_password,
                confirm_password
            )

            if len(errors) > 0:

                for error in errors:
                    st.error(error)

            else:

                st.success(
                    "Account created successfully. "
                    "Please go to the Login tab."
                )
