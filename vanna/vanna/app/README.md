# Text-to-SQL on Vanna (Citi Vertex AI + pgvector + Starburst)

This app builds on the upstream [vanna-ai](https://github.com/vanna-ai/vanna) repo
that's been cloned into `../vanna/vanna/`. We do **not** install vanna from PyPI;
we import its source directly from the clone via `sys.path` (see
`app/__init__.py`).

## Layout

```
test-sql-simple/
  vanna/                 # cloned vanna-ai (untouched)
  reports/               # drop PDFs / PPTX here for ingestion
  app/
    __init__.py          # adds vanna/vanna/src to sys.path
    llm_citi_vertexai.py # CitiVertexAIChat — VannaBase mixin (helix token + custom endpoint)
    db_starburst.py      # connect_to_starburst(vn) — sets vn.run_sql
    ingest_docs.py       # PDF / PPTX → chunks → vn.add_documentation
    ddls.py              # placeholder DDLs to seed pgvector
    train.py             # one-shot: load DDLs + glossary + reports
    main.py              # REPL: ask → generate_sql → run_sql → tabulate
    .env                 # all credentials
    requirements.txt
```

## Setup

```bash
cd test-sql-simple
python -m venv .venv && source .venv/bin/activate
pip install -r app/requirements.txt
```

Fill in `app/.env`:

- `VERTEX_PROJECT`, `VERTEX_ENDPOINT`, `REQUESTS_CA_BUNDLE` — the internal Vertex gateway.
- `PGVECTOR_CONN` — SQLAlchemy URL like `postgresql+psycopg://user:pwd@host:5432/vanna`.
- `STARBURST_HOST`, `STARBURST_USER`, `STARBURST_PASSWORD` (+ optional catalog/schema).

The Vertex auth token is fetched at runtime via `helix auth access-token print -a`,
so the `helix` CLI must be on `PATH` and authenticated.

## Train (load DDLs + reports into pgvector)

Drop any PDFs / `.pptx` files into `reports/`, edit `app/ddls.py` (and optionally
`GLOSSARY` / `QSQL_PAIRS` in `app/train.py`), then:

```bash
python -m app.train
```

This populates three pgvector collections: `ddl`, `documentation`, `sql`.

## Run

```bash
python -m app.main
```

```
Question: How many orders per region last quarter?
SQL:
SELECT c.region, COUNT(*) AS n
FROM orders o JOIN customers c ON c.customer_id = o.customer_id
WHERE o.order_date >= date_add('month', -3, current_date)
GROUP BY c.region
ORDER BY n DESC

+----------+-----+
| region   |   n |
|----------+-----|
| West     | 412 |
| East     | 389 |
+----------+-----+

Question: exit
```

## How the pieces connect

- **LLM**: `CitiVertexAIChat` is a thin subclass of `vanna.legacy.base.VannaBase`
  that implements `system_message`, `user_message`, `assistant_message`, and
  `submit_prompt`. It mirrors `vanna/legacy/google/gemini_chat.py` but calls
  `helix` for the token and points `vertexai.init(...)` at the Citi endpoint.
- **Vector store**: `vanna.legacy.pgvector.PG_VectorStore` (used unchanged).
  Three LangChain `PGVector` collections (`ddl`, `documentation`, `sql`) backed
  by HuggingFace `all-MiniLM-L6-v2` embeddings by default.
- **SQL runner**: `connect_to_starburst(vn)` follows the same monkey-set
  pattern as vanna's built-in `connect_to_snowflake`: it builds a
  `pystarburst.Session` and assigns a closure to `vn.run_sql`. Also sets
  `vn.dialect = "Trino SQL"` so the LLM prompt asks for Trino syntax.
- **Reports**: `ingest_docs.py` extracts text (pypdf / python-pptx), chunks it
  at ~1500 chars with 200 overlap, and pushes chunks via `vn.add_documentation`.
  At question time, vanna retrieves top-N chunks from the `documentation`
  collection alongside related DDLs and Q→SQL examples and stuffs them into
  the SQL-generation prompt.

## Smoke tests

```bash
# 1. Vertex auth + model call
python -c "from app.main import build_vn; vn=build_vn(); print(vn.submit_prompt(['Reply with just READY']))"

# 2. Starburst connectivity
python -c "from app.main import build_vn; from app.db_starburst import connect_to_starburst; vn=build_vn(); connect_to_starburst(vn); print(vn.run_sql('SELECT 1 AS x'))"

# 3. End-to-end
python -m app.train && python -m app.main
```
