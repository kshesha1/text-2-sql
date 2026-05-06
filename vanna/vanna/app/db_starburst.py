"""Starburst (Trino) connector for vanna.

Same pattern as ``VannaBase.connect_to_snowflake`` in vanna/legacy/base/base.py:
build a session, define a closure that calls ``session.sql(...).to_pandas()``,
and assign it to ``vn.run_sql``.
"""

from __future__ import annotations

import os

import pandas as pd
# pyrefly: ignore [missing-import]
from pystarburst import Session


def connect_to_starburst(vn) -> Session:
    """Attach a pystarburst session to ``vn`` and wire ``vn.run_sql``."""
    configs = {
        "host": os.environ["STARBURST_HOST"],
        "port": int(os.environ.get("STARBURST_PORT", 443)),
        "http_scheme": "https",
        "auth": {
            "type": "basic",
            "username": os.environ["STARBURST_USER"],
            "password": os.environ["STARBURST_PASSWORD"],
        },
    }
    catalog = os.environ.get("STARBURST_CATALOG")
    schema = os.environ.get("STARBURST_SCHEMA")
    if catalog:
        configs["catalog"] = catalog
    if schema:
        configs["schema"] = schema

    session = Session.builder.configs(configs).create()

    def run_sql(sql: str) -> pd.DataFrame:
        return session.sql(sql).to_pandas()

    vn.run_sql = run_sql
    vn.run_sql_is_set = True
    vn.dialect = "Trino SQL"
    return session
