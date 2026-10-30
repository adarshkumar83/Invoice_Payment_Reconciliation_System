
import pandas as pd

from decimal import Decimal, InvalidOperation

from database.database import get_connection


# Convert amount into Decimal
def convert_to_decimal(amount):

    try:
        return Decimal(str(amount))
    except InvalidOperation:
        raise ValueError("Invalid monetary amount")


# Confirm a payment allocation
def confirm_allocation(payment_id, invoice_id, allocated_amount, decided_by=None):

    allocated_amount = convert_to_decimal(allocated_amount)

    if allocated_amount <= 0:
        raise ValueError("Allocation amount must be greater than zero")

    connection = get_connection()

    try:
        # Lock database while checking and saving allocation
        connection.execute("BEGIN IMMEDIATE")

        cursor = connection.cursor()

        # Get payment amount
        cursor.execute("""
            SELECT amount
            FROM payments
            WHERE payment_id = ?
        """, (payment_id,))

        payment = cursor.fetchone()

        if payment is None:
            raise ValueError("Payment not found")

        payment_amount = convert_to_decimal(payment[0])

        # Get invoice amount
        cursor.execute("""
            SELECT amount
            FROM invoices
            WHERE invoice_id = ?
        """, (invoice_id,))

        invoice = cursor.fetchone()

        if invoice is None:
            raise ValueError("Invoice not found")

        invoice_amount = convert_to_decimal(invoice[0])

        # Check whether payment already has a confirmed allocation
        cursor.execute("""
            SELECT allocated_amount, status
            FROM allocations
            WHERE payment_id = ?
        """, (payment_id,))

        existing_allocation = cursor.fetchone()

        if existing_allocation is not None:
            if existing_allocation[1] == "confirmed":
                raise ValueError(
                    "This payment is already allocated"
                )

        # Calculate previously allocated payment amount
        cursor.execute("""
            SELECT allocated_amount
            FROM allocations
            WHERE payment_id = ?
            AND status = 'confirmed'
        """, (payment_id,))

        payment_allocations = cursor.fetchall()

        already_allocated = Decimal("0")

        for row in payment_allocations:
            already_allocated += convert_to_decimal(row[0])

        payment_remaining = payment_amount - already_allocated

        if allocated_amount > payment_remaining:
            raise ValueError(
                "Allocation exceeds remaining payment amount"
            )

        # Calculate previously allocated invoice amount
        cursor.execute("""
            SELECT allocated_amount
            FROM allocations
            WHERE invoice_id = ?
            AND status = 'confirmed'
        """, (invoice_id,))

        invoice_allocations = cursor.fetchall()

        invoice_allocated = Decimal("0")

        for row in invoice_allocations:
            invoice_allocated += convert_to_decimal(row[0])

        invoice_remaining = invoice_amount - invoice_allocated

        if allocated_amount > invoice_remaining:
            raise ValueError(
                "Allocation exceeds outstanding invoice amount"
            )

        # Save or update allocation
        if existing_allocation is None:

            cursor.execute("""
                INSERT INTO allocations
                (payment_id, invoice_id, allocated_amount, status, decided_by)
                VALUES (?, ?, ?, 'confirmed', ?)
            """, (
                payment_id,
                invoice_id,
                str(allocated_amount),
                decided_by
            ))

        else:

            cursor.execute("""
                UPDATE allocations
                SET invoice_id = ?,
                    allocated_amount = ?,
                    status = 'confirmed',
                    decision_date = CURRENT_TIMESTAMP,
                    decided_by = ?
                WHERE payment_id = ?
            """, (
                invoice_id,
                str(allocated_amount),
                decided_by,
                payment_id
            ))

        connection.commit()

        return "Payment allocation confirmed successfully"

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()


# Reject a suggested invoice for a payment
def reject_suggestion(payment_id, invoice_id, decided_by=None):

    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute("""
            SELECT status
            FROM allocations
            WHERE payment_id = ?
        """, (payment_id,))

        existing = cursor.fetchone()

        if existing is not None and existing[0] == "confirmed":
            raise ValueError(
                "This payment is already allocated. "
                "Undo the allocation first."
            )

        if existing is None:

            cursor.execute("""
                INSERT INTO allocations
                (payment_id, invoice_id, allocated_amount, status, decided_by)
                VALUES (?, ?, '0.00', 'rejected', ?)
            """, (payment_id, invoice_id, decided_by))

        else:

            cursor.execute("""
                UPDATE allocations
                SET invoice_id = ?,
                    allocated_amount = '0.00',
                    status = 'rejected',
                    decision_date = CURRENT_TIMESTAMP,
                    decided_by = ?
                WHERE payment_id = ?
            """, (invoice_id, decided_by, payment_id))

        connection.commit()

        return "Suggestion rejected"

    finally:
        connection.close()


# Remove a decision so the payment goes back to pending
def undo_decision(payment_id):

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute("""
        DELETE FROM allocations
        WHERE payment_id = ?
    """, (payment_id,))

    connection.commit()
    connection.close()

    return "Decision removed. The payment is pending again."


# Confirm every pending High Confidence suggestion
# Returns (number confirmed, list of problems)
def confirm_high_confidence(decided_by=None):

    review = get_review_table()

    confirmed = 0
    problems = []

    for index, row in review.iterrows():

        if row["status"] != "High Confidence":
            continue

        if row["decision"] != "pending":
            continue

        try:
            confirm_allocation(
                row["payment_id"],
                row["invoice_id"],
                row["payment_amount"],
                decided_by
            )

            confirmed += 1

        except ValueError as error:
            problems.append(row["payment_id"] + ": " + str(error))

    return confirmed, problems


# Calculate outstanding invoice balances
def get_invoice_balances():

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute("""
        SELECT invoice_id, customer_name, amount
        FROM invoices
        ORDER BY invoice_id
    """)

    invoices = cursor.fetchall()

    # Add all confirmed allocations for each invoice
    cursor.execute("""
        SELECT invoice_id, allocated_amount
        FROM allocations
        WHERE status = 'confirmed'
    """)

    paid_totals = {}

    for row in cursor.fetchall():

        previous = paid_totals.get(row[0], Decimal("0"))

        paid_totals[row[0]] = previous + convert_to_decimal(row[1])

    connection.close()

    results = []

    for row in invoices:

        invoice_amount = convert_to_decimal(row[2])

        paid_amount = paid_totals.get(row[0], Decimal("0"))

        outstanding = invoice_amount - paid_amount

        if outstanding <= 0:
            status = "Paid"

        elif paid_amount > 0:
            status = "Partially Paid"

        else:
            status = "Unpaid"

        results.append({
            "invoice_id": row[0],
            "customer_name": row[1],
            "invoice_amount": str(invoice_amount),
            "paid_amount": str(paid_amount),
            "outstanding_amount": str(outstanding),
            "status": status
        })

    return pd.DataFrame(results)


# Calculate unallocated payment balances
def get_payment_balances():

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute("""
        SELECT payment_id, description, amount
        FROM payments
        ORDER BY payment_id
    """)

    payments = cursor.fetchall()

    cursor.execute("""
        SELECT payment_id, allocated_amount
        FROM allocations
        WHERE status = 'confirmed'
    """)

    allocated_totals = {}

    for row in cursor.fetchall():

        previous = allocated_totals.get(row[0], Decimal("0"))

        allocated_totals[row[0]] = previous + convert_to_decimal(row[1])

    connection.close()

    results = []

    for payment in payments:

        payment_amount = convert_to_decimal(payment[2])

        allocated_amount = allocated_totals.get(payment[0], Decimal("0"))

        remaining_amount = payment_amount - allocated_amount

        if remaining_amount <= 0:
            status = "Fully Allocated"

        elif allocated_amount > 0:
            status = "Partially Allocated"

        else:
            status = "Unallocated"

        results.append({
            "payment_id": payment[0],
            "description": payment[1],
            "payment_amount": str(payment_amount),
            "allocated_amount": str(allocated_amount),
            "unallocated_amount": str(remaining_amount),
            "status": status
        })

    return pd.DataFrame(results)


# Generate complete reconciliation report
def get_reconciliation_report():

    invoice_balances = get_invoice_balances()

    payment_balances = get_payment_balances()

    return {
        "invoices": invoice_balances,
        "payments": payment_balances
    }


# Suggestions together with payment, invoice and user decision details
def get_review_table():

    connection = get_connection()

    review = pd.read_sql_query("""
        SELECT
            s.payment_id,
            p.description,
            p.amount AS payment_amount,
            p.payment_date,
            s.invoice_id,
            i.customer_name,
            i.amount AS invoice_amount,
            s.confidence,
            s.status,
            COALESCE(a.status, 'pending') AS decision,
            s.explanation
        FROM match_suggestions s
        JOIN payments p ON p.payment_id = s.payment_id
        LEFT JOIN invoices i ON i.invoice_id = s.invoice_id
        LEFT JOIN allocations a ON a.payment_id = s.payment_id
        ORDER BY s.payment_id
    """, connection)

    connection.close()

    return review


# All saved decisions (confirmed and rejected)
def get_allocation_history():

    connection = get_connection()

    history = pd.read_sql_query("""
        SELECT
            a.allocation_id,
            a.payment_id,
            p.description,
            a.invoice_id,
            i.customer_name,
            a.allocated_amount,
            a.status,
            a.decided_by,
            a.decision_date
        FROM allocations a
        JOIN payments p ON p.payment_id = a.payment_id
        JOIN invoices i ON i.invoice_id = a.invoice_id
        ORDER BY a.decision_date DESC, a.allocation_id DESC
    """, connection)

    connection.close()

    return history


# Total outstanding amount for each customer
def get_customer_summary():

    invoices = get_invoice_balances()

    if invoices.empty:
        return pd.DataFrame()

    for column in ["invoice_amount", "paid_amount", "outstanding_amount"]:
        invoices[column] = pd.to_numeric(invoices[column])

    summary = invoices.groupby("customer_name").agg(
        invoices=("invoice_id", "count"),
        total_invoiced=("invoice_amount", "sum"),
        total_paid=("paid_amount", "sum"),
        total_outstanding=("outstanding_amount", "sum")
    ).reset_index()

    return summary.sort_values("total_outstanding", ascending=False)
