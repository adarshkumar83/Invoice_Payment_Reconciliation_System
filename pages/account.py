
import streamlit as st

from modules.auth import change_password

from modules.ui import current_user
from modules.ui import require_login
from modules.ui import logout_session


require_login()

user = current_user()

st.title("👤 My Account")

st.subheader("Profile")

st.write("**Name:**", user["full_name"])

st.write("**Username:**", user["username"])

st.write("**Email:**", user["email"])

st.write("**Member since:**", str(user["created_at"])[:10])

st.divider()


# Change password
st.subheader("Change Password")

with st.form("password_form", clear_on_submit=True):

    old_password = st.text_input("Current password", type="password")

    new_password = st.text_input(
        "New password",
        type="password",
        help="At least 8 characters with a letter and a number"
    )

    confirm_password = st.text_input("Confirm new password", type="password")

    saved = st.form_submit_button("Update Password", type="primary")

if saved:

    errors = change_password(
        user["username"],
        old_password,
        new_password,
        confirm_password
    )

    if len(errors) > 0:

        for error in errors:
            st.error(error)

    else:

        st.success("Password updated successfully.")

st.divider()


# Logout
st.subheader("Logout")

if st.button("Logout"):

    logout_session()

    st.rerun()
