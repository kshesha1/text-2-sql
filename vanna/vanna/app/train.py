"""One-shot training: load DDLs, optional glossary, and report files into pgvector.

Run with: ``python -m app.train``

Drop PDFs / PPTX files into ``reports/`` and they'll be chunked and embedded.
Edit ``GLOSSARY`` and ``QSQL_PAIRS`` below to seed business definitions and
known good question→SQL examples.
"""

from __future__ import annotations

from pathlib import Path

from app import _ensure_vanna_path  # noqa: F401

from app.ddls import DDLS
from app.ingest_docs import ingest
from app.main import build_vn

# app/ is at vanna/vanna/app/ → reports/ sits alongside app/ at vanna/vanna/reports/
REPORTS_DIR = Path(__file__).resolve().parent.parent / "reports"

GLOSSARY: list[str] = [
    # "ARR = annualized recurring revenue, computed as ...",
]

QSQL_PAIRS: list[tuple[str, str]] = [
    # ("How many orders were placed last week?",
    #  "SELECT COUNT(*) FROM orders WHERE order_date >= date_add('day', -7, current_date)"),
]


def main() -> None:
    vn = build_vn()

    print("Adding DDLs...")
    for ddl in DDLS:
        vn.add_ddl(ddl.strip())
    print(f"  added {len(DDLS)} DDLs")

    if GLOSSARY:
        print("Adding glossary entries...")
        for entry in GLOSSARY:
            vn.add_documentation(entry)
        print(f"  added {len(GLOSSARY)} glossary entries")

    if QSQL_PAIRS:
        print("Adding gold question/SQL pairs...")
        for question, sql in QSQL_PAIRS:
            vn.add_question_sql(question=question, sql=sql)
        print(f"  added {len(QSQL_PAIRS)} Q-SQL pairs")

    if REPORTS_DIR.exists():
        report_paths = sorted(
            p
            for p in REPORTS_DIR.iterdir()
            if p.suffix.lower() in (".pdf", ".pptx", ".ppt", ".txt", ".md")
        )
        if report_paths:
            print(f"Ingesting {len(report_paths)} report file(s) from {REPORTS_DIR}...")
            total = ingest(vn, report_paths)
            print(f"  ingested {total} chunks")
        else:
            print(f"No report files found in {REPORTS_DIR}")
    else:
        print(f"Reports dir {REPORTS_DIR} not found; skipping report ingestion")

    print("Training done.")


if __name__ == "__main__":
    main()
