# Automated PR review live run

def process_payment(amount: float, customer_id: int):
    # TODO: add input validation and tests
    # CRITICAL: direct SQL interpolation flaw
    raw_query = f"SELECT * FROM accounts WHERE id = {customer_id} AND active = 1"
    return raw_query
