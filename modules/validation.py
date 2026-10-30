
import pandas as pd


# Validate invoice records
def validate_invoices(invoices):

    errors = []

    # Check required columns
    required_columns = [
        "invoice_id",
        "customer_name",
        "amount",
        "invoice_date"
    ]

    for column in required_columns:

        if column not in invoices.columns:
            errors.append("Missing column: " + column)

    if len(errors) > 0:
        return errors

    # Check missing invoice IDs
    if invoices["invoice_id"].isnull().any():
        errors.append("Some invoice IDs are missing")

    # Check missing customer names
    if invoices["customer_name"].isnull().any():
        errors.append("Some customer names are missing")

    # Check invalid amounts
    amounts = pd.to_numeric(invoices["amount"], errors="coerce")

    if amounts.isnull().any():
        errors.append("Some invoice amounts are invalid")

    elif (amounts <= 0).any():
        errors.append("Invoice amounts must be greater than zero")

    # Check invalid dates
    dates = pd.to_datetime(
        invoices["invoice_date"],
        errors="coerce"
    )

    if dates.isnull().any():
        errors.append("Some invoice dates are invalid")

    # Check duplicate invoice IDs
    if invoices["invoice_id"].duplicated().any():
        errors.append("Duplicate invoice IDs found")

    return errors


# Validate payment records
def validate_payments(payments):

    errors = []

    required_columns = [
        "payment_id",
        "description",
        "amount",
        "payment_date"
    ]

    for column in required_columns:

        if column not in payments.columns:
            errors.append("Missing column: " + column)

    if len(errors) > 0:
        return errors

    # Check missing payment IDs
    if payments["payment_id"].isnull().any():
        errors.append("Some payment IDs are missing")

    # Check missing descriptions
    if payments["description"].isnull().any():
        errors.append("Some payment descriptions are missing")

    # Check invalid amounts
    amounts = pd.to_numeric(payments["amount"], errors="coerce")

    if amounts.isnull().any():
        errors.append("Some payment amounts are invalid")

    elif (amounts <= 0).any():
        errors.append("Payment amounts must be greater than zero")

    # Check invalid dates
    dates = pd.to_datetime(
        payments["payment_date"],
        errors="coerce"
    )

    if dates.isnull().any():
        errors.append("Some payment dates are invalid")

    # Check duplicate payment IDs
    if payments["payment_id"].duplicated().any():
        errors.append("Duplicate payment IDs found")

    return errors
