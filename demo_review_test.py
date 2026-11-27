# Automated PR review demo test

def process_payment(amount: float, customer_id: int):
    # TODO: add input validation and unit tests
    # Potential SQL injection risk:
    raw_query = f"SELECT * FROM accounts WHERE id = {customer_id} AND active = 1"
    return raw_query
