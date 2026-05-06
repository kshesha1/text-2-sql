import os
from pystarburst import Session
from pystarburst.functions import col


def get_session() -> Session:
    host = os.environ["STARBURST_HOST"]
    port = int(os.environ.get("STARBURST_PORT", 443))
    user = os.environ["STARBURST_USER"]
    password = os.environ["STARBURST_PASSWORD"]
    catalog = os.environ.get("STARBURST_CATALOG", "")
    schema = os.environ.get("STARBURST_SCHEMA", "")

    session_properties = {
        "host": host,
        "port": port,
        "http_scheme": "https",
        "auth": {"type": "basic", "username": user, "password": password},
    }

    if catalog:
        session_properties["catalog"] = catalog
    if schema:
        session_properties["schema"] = schema

    return Session.builder.configs(session_properties).create()


def run_query(session: Session, sql: str):
    """Execute SQL and return (columns, rows)."""
    df = session.sql(sql).to_pandas()
    return list(df.columns), df.values.tolist()
