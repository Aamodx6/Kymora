# Updated test utility for review agent demo

def process_payment(amount: float, customer_id: int):
    # Todo: add unit tests
    # Flagged for quality review
    # Potential SQL risk:
    raw_query = f"SELECT * FROM accounts WHERE id = {customer_id}"
    return raw_query
