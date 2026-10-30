

# Find payments that look like the same payment entered twice
# (same description, amount and date)
# Returns a dictionary: {duplicate_payment_id: first_payment_id}
def find_duplicate_payments(payments):

    first_seen = {}

    duplicates = {}

    for index, row in payments.iterrows():

        key = (
            str(row["description_key"]),
            str(row["amount"]),
            str(row["payment_date"])
        )

        if key in first_seen:
            duplicates[row["payment_id"]] = first_seen[key]

        else:
            first_seen[key] = row["payment_id"]

    return duplicates
