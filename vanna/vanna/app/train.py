"""One-shot training: load DDLs, optional glossary, and report files into pgvector.

Run with: ``python -m app.train``

Drop PDFs / PPTX files into ``reports/`` and they'll be chunked and embedded.
Edit ``GLOSSARY`` and ``QSQL_PAIRS`` below to seed business definitions and
known good question→SQL examples.
"""

from __future__ import annotations

import sys
from pathlib import Path

print("Step 1/5: importing packages...", flush=True)

from app import _ensure_vanna_path  # noqa: F401

from app.ddls import DDLS
from app.ingest_docs import ingest

print("Step 2/5: packages loaded.", flush=True)

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
    print("Step 3/5: connecting to Vertex AI + pgvector...", flush=True)
    try:
        # Import here (not at top) so Step 1/2 always print before any
        # heavy connection attempt (helix token fetch, pgvector handshake).
        from app.main import build_vn
        vn = build_vn()
    except Exception as exc:
        print(f"\n[FAILED] Could not initialise vanna: {exc}", flush=True)
        import traceback
        traceback.print_exc()
        sys.exit(1)

    print("Step 3/5: connected.\n", flush=True)

    # --- DDLs ---
    print(f"Step 4/5: adding {len(DDLS)} DDL(s)...", flush=True)
    for i, ddl in enumerate(DDLS, start=1):
        try:
            vn.add_ddl(ddl.strip())
            print(f"  [{i}/{len(DDLS)}] OK", flush=True)
        except Exception as exc:
            print(f"  [{i}/{len(DDLS)}] FAILED: {exc}", flush=True)

    # --- Glossary ---
    if GLOSSARY:
        print(f"\nAdding {len(GLOSSARY)} glossary entry/entries...", flush=True)
        for entry in GLOSSARY:
            try:
                vn.add_documentation(entry)
            except Exception as exc:
                print(f"  FAILED: {exc}", flush=True)
        print(f"  done ({len(GLOSSARY)} entries)", flush=True)

    # --- Gold Q→SQL pairs ---
    if QSQL_PAIRS:
        print(f"\nAdding {len(QSQL_PAIRS)} Q→SQL pair(s)...", flush=True)
        for question, sql in QSQL_PAIRS:
            try:
                vn.add_question_sql(question=question, sql=sql)
            except Exception as exc:
                print(f"  FAILED ({question!r}): {exc}", flush=True)
        print(f"  done ({len(QSQL_PAIRS)} pairs)", flush=True)

    # --- Reports ---
    print(f"\nStep 5/5: scanning {REPORTS_DIR} for reports...", flush=True)
    if REPORTS_DIR.exists():
        report_paths = sorted(
            p
            for p in REPORTS_DIR.iterdir()
            if p.suffix.lower() in (".pdf", ".pptx", ".ppt", ".txt", ".md")
        )
        if report_paths:
            print(f"  found {len(report_paths)} file(s), ingesting...", flush=True)
            total = ingest(vn, report_paths)
            print(f"  ingested {total} total chunks", flush=True)
        else:
            print(f"  no files found in {REPORTS_DIR} — skipping", flush=True)
    else:
        print(f"  {REPORTS_DIR} does not exist — skipping", flush=True)

    print("\nTraining done.", flush=True)


if __name__ == "__main__":
    main()
