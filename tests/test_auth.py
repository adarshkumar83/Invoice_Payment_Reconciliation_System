
from modules.auth import hash_password
from modules.auth import verify_password
from modules.auth import register_user
from modules.auth import authenticate
from modules.auth import change_password
from modules.auth import MAX_FAILED_ATTEMPTS


def create(username="adarsh", password="Secret123"):

    return register_user(
        username, "Adarsh Kumar", "adarsh@example.com", password, password
    )


def test_password_hash():

    saved = hash_password("Secret123")

    assert "Secret123" not in saved
    assert verify_password("Secret123", saved)
    assert not verify_password("secret123", saved)

    # Same password gives a different hash (random salt)
    assert saved != hash_password("Secret123")


def test_register_and_login(db):

    assert create() == []

    user, error = authenticate("  ADARSH ", "Secret123")

    assert user["username"] == "adarsh"
    assert error == ""


def test_register_rules(db):

    errors = register_user("a!", "", "bad", "short", "different")

    assert len(errors) >= 5

    create()

    assert create() == ["This username is already taken"]


def test_wrong_password_and_unknown_user(db):

    create()

    user, error = authenticate("adarsh", "wrongpass1")
    assert user is None and error == "Invalid username or password"

    user, error = authenticate("nobody", "Secret123")
    assert user is None and error == "Invalid username or password"


def test_account_locks_after_too_many_failures(db):

    create()

    for number in range(MAX_FAILED_ATTEMPTS):
        authenticate("adarsh", "wrongpass1")

    # Even the right password is refused while locked
    user, error = authenticate("adarsh", "Secret123")

    assert user is None
    assert "Too many failed attempts" in error


def test_change_password(db):

    create()

    assert change_password("adarsh", "bad", "NewSecret1", "NewSecret1") == [
        "Current password is incorrect"
    ]

    assert change_password("adarsh", "Secret123", "short", "short") != []

    assert change_password("adarsh", "Secret123", "NewSecret1", "NewSecret1") == []

    assert authenticate("adarsh", "Secret123")[0] is None
    assert authenticate("adarsh", "NewSecret1")[0] is not None
