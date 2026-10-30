
import re
import hmac
import hashlib
import secrets

from datetime import datetime, timedelta

from database.database import save_user
from database.database import get_user
from database.database import update_password
from database.database import update_login_state


# Password hashing settings
HASH_ROUNDS = 200000

# Login lock settings
MAX_FAILED_ATTEMPTS = 5
LOCK_MINUTES = 5


# Create a safe password hash (salt + pbkdf2)
def hash_password(password):

    salt = secrets.token_hex(16)

    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        HASH_ROUNDS
    )

    return salt + "$" + digest.hex()


# Check a password against the saved hash
def verify_password(password, saved_hash):

    try:
        salt, saved_digest = saved_hash.split("$")
    except ValueError:
        return False

    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        HASH_ROUNDS
    )

    return hmac.compare_digest(digest.hex(), saved_digest)


# Check password rules
def validate_password(password):

    errors = []

    if len(password) < 8:
        errors.append("Password must be at least 8 characters")

    if not re.search(r"[A-Za-z]", password):
        errors.append("Password must contain a letter")

    if not re.search(r"[0-9]", password):
        errors.append("Password must contain a number")

    return errors


# Check registration details
def validate_registration(username, full_name, email, password, confirm_password):

    errors = []

    if not re.fullmatch(r"[A-Za-z0-9_]{3,30}", username.strip()):
        errors.append(
            "Username must be 3-30 characters "
            "(letters, numbers and underscore only)"
        )

    if len(full_name.strip()) < 2:
        errors.append("Please enter your full name")

    if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email.strip()):
        errors.append("Please enter a valid email address")

    errors.extend(validate_password(password))

    if password != confirm_password:
        errors.append("Passwords do not match")

    return errors


# Create a new account (returns a list of errors)
def register_user(username, full_name, email, password, confirm_password):

    errors = validate_registration(
        username,
        full_name,
        email,
        password,
        confirm_password
    )

    if len(errors) > 0:
        return errors

    username = username.strip().lower()

    if get_user(username) is not None:
        return ["This username is already taken"]

    save_user(
        username,
        full_name.strip(),
        email.strip().lower(),
        hash_password(password)
    )

    return []


# Login check. Returns (user, error message)
def authenticate(username, password):

    username = username.strip().lower()

    user = get_user(username)

    # Same message for unknown user and wrong password
    wrong_message = "Invalid username or password"

    if user is None:
        return None, wrong_message

    # Check whether the account is locked
    if user["locked_until"]:

        locked_until = datetime.fromisoformat(user["locked_until"])

        if datetime.now() < locked_until:
            return None, (
                "Too many failed attempts. "
                "Please try again in a few minutes."
            )

    if verify_password(password, user["password_hash"]):

        update_login_state(username, 0, None)

        return user, ""

    # Wrong password: count the failed attempt
    attempts = user["failed_attempts"] + 1

    locked_until = None

    if attempts >= MAX_FAILED_ATTEMPTS:

        locked_until = (
            datetime.now() + timedelta(minutes=LOCK_MINUTES)
        ).isoformat()

        attempts = 0

    update_login_state(username, attempts, locked_until)

    return None, wrong_message


# Change password (returns a list of errors)
def change_password(username, old_password, new_password, confirm_password):

    user = get_user(username)

    if user is None:
        return ["User not found"]

    if not verify_password(old_password, user["password_hash"]):
        return ["Current password is incorrect"]

    errors = validate_password(new_password)

    if new_password != confirm_password:
        errors.append("New passwords do not match")

    if len(errors) > 0:
        return errors

    update_password(username, hash_password(new_password))

    return []
