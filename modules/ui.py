
import streamlit as st
import pandas as pd


# Format money in rupees
def money(amount):

    return f"₹{float(amount):,.2f}"


# Convert text columns into numbers (for sorting and totals)
def to_numbers(data, columns):

    data = data.copy()

    for column in columns:

        if column in data.columns:
            data[column] = pd.to_numeric(data[column])

    return data


# Keep a message so it is still visible after st.rerun()
def set_message(kind, text):

    st.session_state["message"] = (kind, text)


# Show (and clear) the saved message
def show_message():

    message = st.session_state.pop("message", None)

    if message is None:
        return

    kind, text = message

    if kind == "success":
        st.success(text)

    elif kind == "warning":
        st.warning(text)

    else:
        st.error(text)


# Current logged in user (None if not logged in)
def current_user():

    return st.session_state.get("user")


# Stop the page if nobody is logged in
def require_login():

    if current_user() is None:

        st.warning("Please login to continue.")

        st.stop()


# Save the user in the session after login
def login_session(user):

    st.session_state["user"] = {
        "username": user["username"],
        "full_name": user["full_name"],
        "email": user["email"],
        "created_at": user["created_at"]
    }


# Clear the session on logout
def logout_session():

    st.session_state.clear()
