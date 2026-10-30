
import pandas as pd
import re

from datetime import datetime

from rapidfuzz import fuzz

from modules.normalization import normalize_invoices
from modules.normalization import normalize_payments
from modules.duplicates import find_duplicate_payments


# Remove invoice and payment numbers from a description
# Example: "transfer rahul verma inv101" -> "transfer rahul verma"
def remove_reference_words(description):

    words = []

    for word in str(description).split():

        if not re.fullmatch(r"(inv|pay)\d+", word):
            words.append(word)

    return " ".join(words)


# Calculate customer name similarity (0 - 100)
def calculate_name_similarity(customer_name, description):

    description = remove_reference_words(description)

    if customer_name == "" or description == "":
        return 0

    # partial_ratio also works when the description has extra words
    # or only a short name like "Nisha D"
    score = fuzz.partial_ratio(
        str(customer_name),
        description
    )

    return score


# Check invoice reference inside payment description
def check_invoice_reference(invoice_id, description):

    invoice_id = str(invoice_id)
    description = str(description)

    pattern = r"\b" + re.escape(invoice_id) + r"\b"

    if re.search(pattern, description):
        return True

    return False


# Convert text into a date (fast for YYYY-MM-DD, slower for other formats)
def to_date(value):

    try:
        return datetime.fromisoformat(str(value)[:10])

    except ValueError:

        converted = pd.to_datetime(value, errors="coerce")

        if pd.isna(converted):
            return None

        return converted.to_pydatetime()


# Calculate date similarity
def calculate_date_score(invoice_date, payment_date):

    invoice_date = to_date(invoice_date)
    payment_date = to_date(payment_date)

    if invoice_date is None or payment_date is None:
        return 0

    difference = abs((payment_date - invoice_date).days)

    if difference <= 1:
        return 100

    elif difference <= 3:
        return 80

    elif difference <= 7:
        return 60

    elif difference <= 14:
        return 40

    else:
        return 0


# Calculate complete matching score
def calculate_matching_score(invoice, payment):

    # Check invoice reference
    reference_match = check_invoice_reference(
        invoice["invoice_key"],
        payment["description_key"]
    )

    if reference_match:
        reference_score = 100

    else:
        reference_score = 0

    # Calculate customer similarity
    customer_score = calculate_name_similarity(
        invoice["customer_key"],
        payment["description_key"]
    )

    # Compare amounts
    invoice_amount = float(invoice["amount"])
    payment_amount = float(payment["amount"])

    if invoice_amount == payment_amount:
        amount_score = 100

    else:
        amount_score = 0

    # Calculate date score
    date_score = calculate_date_score(
        invoice["invoice_date"],
        payment["payment_date"]
    )

    # Calculate final confidence score
    confidence = (
        reference_score * 0.40
        + customer_score * 0.30
        + amount_score * 0.20
        + date_score * 0.10
    )

    return {
        "reference_match": reference_match,
        "customer_similarity": round(customer_score, 2),
        "amount_match": invoice_amount == payment_amount,
        "date_score": date_score,
        "confidence": round(confidence, 2)
    }


# Explain the difference between payment and invoice amounts
def describe_amount(invoice_amount, payment_amount):

    difference = float(payment_amount) - float(invoice_amount)

    if difference == 0:
        return "Exact amount match"

    if difference < 0:
        return (
            "Amount mismatch (short payment of "
            + f"{abs(difference):,.2f})"
        )

    return (
        "Amount mismatch (overpayment of "
        + f"{difference:,.2f})"
    )


# Generate matching suggestions
def suggest_matches(invoices, payments):

    # Make sure the matching columns exist
    if "invoice_key" not in invoices.columns:
        invoices = normalize_invoices(invoices)

    if "description_key" not in payments.columns:
        payments = normalize_payments(payments)

    # Find payments entered twice
    duplicates = find_duplicate_payments(payments)

    suggestions = []

    invoice_list = invoices.to_dict("records")

    # Check every payment against every invoice
    for payment in payments.to_dict("records"):

        candidates = []

        for invoice in invoice_list:

            result = calculate_matching_score(
                invoice,
                payment
            )

            # Save candidate details
            candidates.append({
                "payment_id": payment["payment_id"],
                "invoice_id": invoice["invoice_id"],
                "invoice_amount": invoice["amount"],
                "payment_amount": payment["amount"],
                "reference_match": result["reference_match"],
                "customer_similarity": result["customer_similarity"],
                "amount_match": result["amount_match"],
                "date_score": result["date_score"],
                "confidence": result["confidence"]
            })

        # Check whether candidates exist
        if len(candidates) == 0:

            suggestions.append({
                "payment_id": payment["payment_id"],
                "invoice_id": None,
                "confidence": 0,
                "status": "Unmatched",
                "explanation": "No invoice records available"
            })

            continue

        # Sort candidates by confidence
        candidates.sort(
            key=lambda item: item["confidence"],
            reverse=True
        )

        # Get the best matching candidate
        best_match = candidates[0]

        # Check for ambiguous matches
        ambiguous = False

        if len(candidates) > 1:

            second_match = candidates[1]

            score_difference = (
                best_match["confidence"]
                - second_match["confidence"]
            )

            if score_difference < 10:
                ambiguous = True

        # Create matching explanation
        explanation = []

        if best_match["reference_match"]:
            explanation.append("Invoice reference matched")

        explanation.append(
            "Customer similarity: "
            + str(best_match["customer_similarity"])
            + "%"
        )

        explanation.append(
            describe_amount(
                best_match["invoice_amount"],
                best_match["payment_amount"]
            )
        )

        if ambiguous:
            explanation.append("Other invoices look almost the same")

        # Decide the status
        if payment["payment_id"] in duplicates:
            status = "Possible Duplicate"

            explanation.append(
                "Same description, amount and date as "
                + str(duplicates[payment["payment_id"]])
            )

        elif ambiguous:
            status = "Ambiguous"

        elif not best_match["amount_match"]:
            status = "Amount Mismatch"

        elif best_match["confidence"] >= 85:
            status = "High Confidence"

        elif best_match["confidence"] >= 60:
            status = "Needs Review"

        else:
            status = "Unmatched"

        # Save final suggestion
        suggestions.append({
            "payment_id": best_match["payment_id"],
            "invoice_id": best_match["invoice_id"],
            "invoice_amount": best_match["invoice_amount"],
            "payment_amount": best_match["payment_amount"],
            "reference_match": best_match["reference_match"],
            "customer_similarity": best_match["customer_similarity"],
            "amount_match": best_match["amount_match"],
            "date_score": best_match["date_score"],
            "confidence": best_match["confidence"],
            "status": status,
            "explanation": ", ".join(explanation)
        })

    return pd.DataFrame(suggestions)
