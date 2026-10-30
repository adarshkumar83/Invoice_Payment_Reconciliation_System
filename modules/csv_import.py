
import pandas as pd


# Import invoice records
def import_invoices(file):

    invoices = pd.read_csv(file)

    return invoices


# Import payment records
def import_payments(file):

    payments = pd.read_csv(file)

    return payments
