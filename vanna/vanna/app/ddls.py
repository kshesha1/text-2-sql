"""Hardcoded DDLs to seed vanna's training set. Swap with the real schemas."""

DDLS = [
    """
    CREATE TABLE orders (
        order_id BIGINT,
        customer_id BIGINT,
        order_date DATE,
        total_amount DECIMAL(10,2),
        status VARCHAR
    );
    """,
    """
    CREATE TABLE customers (
        customer_id BIGINT,
        name VARCHAR,
        email VARCHAR,
        region VARCHAR
    );
    """,
]
