"""REPL entry point: ask a natural-language question, run generated SQL, print result."""

from __future__ import annotations

import os
import pathlib

# pyrefly: ignore [missing-import]
from app import _ensure_vanna_path  # noqa: F401  (sys.path side effect)

from dotenv import load_dotenv

# .env lives in the same app/ directory regardless of where the REPL is launched from
load_dotenv(pathlib.Path(__file__).resolve().parent / ".env")

from tabulate import tabulate

from vanna.legacy.pgvector import PG_VectorStore

# pyrefly: ignore [missing-import]
from app.db_starburst import connect_to_starburst
# pyrefly: ignore [missing-import]
from app.llm_citi_vertexai import CitiVertexAIChat


class MyVanna(CitiVertexAIChat, PG_VectorStore):
    """Composed vanna instance: Citi Vertex AI + pgvector."""

    pass


def build_vn() -> MyVanna:
    config = {
        # PG_VectorStore
        "connection_string": os.environ["PGVECTOR_CONN"],
        "n_results": int(os.environ.get("PGVECTOR_N_RESULTS", "10")),
        # CitiVertexAIChat
        "project": os.environ["VERTEX_PROJECT"],
        "api_endpoint": os.environ["VERTEX_ENDPOINT"],
        "ca_bundle": os.environ.get("REQUESTS_CA_BUNDLE", ""),
        "model_name": os.environ.get("VERTEX_MODEL", "gemini-2.0-flash-001"),
        "temperature": float(os.environ.get("VERTEX_TEMPERATURE", "0.2")),
    }
    return MyVanna(config=config)


def main() -> None:
    print("Starting up...")
    vn = build_vn()
    connect_to_starburst(vn)
    print("Ready. Type your question (or 'exit' to quit).\n")

    while True:
        try:
            question = input("Question: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nBye!")
            break

        if not question:
            continue
        if question.lower() in ("exit", "quit"):
            print("Bye!")
            break

        try:
            sql = vn.generate_sql(question)
        except Exception as exc:
            print(f"[error] SQL generation failed: {exc}\n")
            continue

        print(f"\nSQL:\n{sql}\n")

        try:
            df = vn.run_sql(sql)
            if df is None or df.empty:
                print("(no rows returned)")
            else:
                print(tabulate(df, headers=df.columns, tablefmt="psql", showindex=False))
        except Exception as exc:
            print(f"[error] Query failed: {exc}")

        print()


if __name__ == "__main__":
    main()
