# Text-to-SQL Agent

Ask questions in plain English, get SQL run against Starburst, see results in a table.

## Setup

**1. Install dependencies**
```bash
cd text_to_sql
pip install -r requirements.txt
```

**2. Fill in `.env`**
```
ANTHROPIC_API_KEY=sk-ant-...

STARBURST_HOST=your-host.trino.example.com
STARBURST_PORT=443
STARBURST_USER=your_username
STARBURST_PASSWORD=your_password
STARBURST_CATALOG=your_catalog   # optional
STARBURST_SCHEMA=your_schema     # optional
```

**3. Swap in your DDLs**

Edit `ddls.py` — replace the placeholder `CREATE TABLE` statements with your real table definitions.

**4. Run**
```bash
python main.py
```

## Usage

```
Connected. Type your question (or 'exit' to quit).

Question: How many orders are there per region?
Generating SQL...

SQL:
SELECT c.region, COUNT(o.order_id) AS order_count
FROM orders o
JOIN customers c ON o.customer_id = c.customer_id
GROUP BY c.region
ORDER BY order_count DESC

+----------+--------------+
| region   |   order_count|
|----------+--------------|
| West     |          412 |
| East     |          389 |
+----------+--------------+

Question: exit
Bye!
```

## Files

| File | Purpose |
|------|---------|
| `main.py` | REPL loop — connects, reads input, prints results |
| `agent.py` | Calls Claude, extracts SQL from response |
| `db.py` | pystarburst session + query runner |
| `ddls.py` | Hardcoded table DDLs sent to Claude |
| `.env` | Credentials (never commit this) |
