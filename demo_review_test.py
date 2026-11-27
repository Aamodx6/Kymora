# Sample utility function for review agent demonstration

def fetch_user_data(user_id: int):
    # Missing docstring and missing test coverage
    # Security note: demo safe query pattern
    query = f"SELECT * FROM users WHERE id = {user_id}"
    return query
