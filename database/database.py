
import sqlite3
import os
import pandas as pd


# Get the main project directory
BASE_DIR = os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)

# Database file location
# (FAIRSHIFT_DB can be used to point to another file, e.g. for tests)
DB_PATH = os.environ.get(
    "FAIRSHIFT_DB",
    os.path.join(BASE_DIR, "database", "reconciliation.db")
)


# Connect to SQLite database
def get_connection():
    connection = sqlite3.connect(DB_PATH)

    # Enable foreign key checking
    connection.execute("PRAGMA foreign_keys = ON")

    return connection


# Create all database tables
def create_tables():

    connection = get_connection()
    cursor = connection.cursor()

    # User table (login accounts)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            full_name TEXT NOT NULL,
            email TEXT NOT NULL,
            password_hash TEXT NOT NULL,
            failed_attempts INTEGER NOT NULL DEFAULT 0,
            locked_until TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Invoice table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS invoices (
            invoice_id TEXT PRIMARY KEY,
            customer_name TEXT NOT NULL,
            amount TEXT NOT NULL,
            invoice_date TEXT NOT NULL
        )
    """)

    # Payment table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS payments (
            payment_id TEXT PRIMARY KEY,
            description TEXT NOT NULL,
            amount TEXT NOT NULL,
            payment_date TEXT NOT NULL
        )
    """)

    # Matching suggestions table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS match_suggestions (
            payment_id TEXT PRIMARY KEY,
            invoice_id TEXT,
            confidence REAL,
            status TEXT,
            explanation TEXT,

            FOREIGN KEY (payment_id)
                REFERENCES payments(payment_id),

            FOREIGN KEY (invoice_id)
                REFERENCES invoices(invoice_id)
        )
    """)

    # Allocation and user decision table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS allocations (
            allocation_id INTEGER PRIMARY KEY AUTOINCREMENT,
            payment_id TEXT UNIQUE NOT NULL,
            invoice_id TEXT NOT NULL,
            allocated_amount TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'pending',
            decision_date TEXT DEFAULT CURRENT_TIMESTAMP,
            decided_by TEXT,

            CHECK (status IN ('pending', 'confirmed', 'rejected')),

            FOREIGN KEY (payment_id)
                REFERENCES payments(payment_id),

            FOREIGN KEY (invoice_id)
                REFERENCES invoices(invoice_id)
        )
    """)

    # Older databases do not have the decided_by column
    cursor.execute("PRAGMA table_info(allocations)")

    columns = []

    for column in cursor.fetchall():
        columns.append(column[1])

    if "decided_by" not in columns:
        cursor.execute(
            "ALTER TABLE allocations ADD COLUMN decided_by TEXT"
        )

    connection.commit()
    connection.close()


# ---------------------------------------------------------------
# User records
# ---------------------------------------------------------------

# Save a new user
def save_user(username, full_name, email, password_hash):

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        INSERT INTO users
        (username, full_name, email, password_hash)
        VALUES (?, ?, ?, ?)
    """, (username, full_name, email, password_hash))

    connection.commit()
    connection.close()


# Get one user by username (returns None if not found)
def get_user(username):

    connection = get_connection()
    connection.row_factory = sqlite3.Row

    cursor = connection.cursor()

    cursor.execute(
        "SELECT * FROM users WHERE username = ?",
        (username,)
    )

    row = cursor.fetchone()

    connection.close()

    if row is None:
        return None

    return dict(row)


# Count registered users
def count_users():

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("SELECT COUNT(*) FROM users")

    total = cursor.fetchone()[0]

    connection.close()

    return total


# Update the saved password
def update_password(username, password_hash):

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        UPDATE users
        SET password_hash = ?
        WHERE username = ?
    """, (password_hash, username))

    connection.commit()
    connection.close()


# Save failed login attempts and lock time
def update_login_state(username, failed_attempts, locked_until):

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        UPDATE users
        SET failed_attempts = ?,
            locked_until = ?
        WHERE username = ?
    """, (failed_attempts, locked_until, username))

    connection.commit()
    connection.close()


# ---------------------------------------------------------------
# Invoice, payment and suggestion records
# ---------------------------------------------------------------

# Save invoice records
def save_invoices(invoices):

    connection = get_connection()
    cursor = connection.cursor()

    for index, row in invoices.iterrows():

        cursor.execute("""
            INSERT OR REPLACE INTO invoices
            (invoice_id, customer_name, amount, invoice_date)
            VALUES (?, ?, ?, ?)
        """, (
            str(row["invoice_id"]),
            str(row["customer_name"]),
            str(row["amount"]),
            str(row["invoice_date"])
        ))

    connection.commit()
    connection.close()


# Save payment records
def save_payments(payments):

    connection = get_connection()
    cursor = connection.cursor()

    for index, row in payments.iterrows():

        cursor.execute("""
            INSERT OR REPLACE INTO payments
            (payment_id, description, amount, payment_date)
            VALUES (?, ?, ?, ?)
        """, (
            str(row["payment_id"]),
            str(row["description"]),
            str(row["amount"]),
            str(row["payment_date"])
        ))

    connection.commit()
    connection.close()


# Save matching suggestions
def save_suggestions(suggestions):

    connection = get_connection()
    cursor = connection.cursor()

    for index, row in suggestions.iterrows():

        invoice_id = row["invoice_id"]

        if pd.isna(invoice_id):
            invoice_id = None

        cursor.execute("""
            INSERT OR REPLACE INTO match_suggestions
            (payment_id, invoice_id, confidence, status, explanation)
            VALUES (?, ?, ?, ?, ?)
        """, (
            str(row["payment_id"]),
            invoice_id,
            float(row["confidence"]),
            str(row["status"]),
            str(row["explanation"])
        ))

    connection.commit()
    connection.close()


# Get all invoices
def get_invoices():

    connection = get_connection()

    invoices = pd.read_sql_query(
        "SELECT * FROM invoices ORDER BY invoice_id",
        connection
    )

    connection.close()

    return invoices


# Get all payments
def get_payments():

    connection = get_connection()

    payments = pd.read_sql_query(
        "SELECT * FROM payments ORDER BY payment_id",
        connection
    )

    connection.close()

    return payments


# Get all matching suggestions
def get_suggestions():

    connection = get_connection()

    suggestions = pd.read_sql_query(
        "SELECT * FROM match_suggestions ORDER BY payment_id",
        connection
    )

    connection.close()

    return suggestions


# Delete all invoices, payments, suggestions and decisions
# (user accounts are kept)
def clear_all_data():

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("DELETE FROM allocations")
    cursor.execute("DELETE FROM match_suggestions")
    cursor.execute("DELETE FROM payments")
    cursor.execute("DELETE FROM invoices")

    connection.commit()
    connection.close()
