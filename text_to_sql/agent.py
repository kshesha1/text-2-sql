import re
import anthropic
from ddls import DDLS

client = anthropic.Anthropic()

SYSTEM_PROMPT = (
    "You are a SQL expert. Given the following table DDLs and a user question, "
    "return ONLY a valid Trino/Starburst SQL query with no explanation, "
    "no markdown, no code fences. Just raw SQL."
)


def get_sql(question: str) -> str:
    user_message = f"DDLs:\n{DDLS}\n\nQuestion: {question}"

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_message}],
    )

    raw = response.content[0].text

    match = re.search(r"```sql\n?(.*?)```", raw, re.DOTALL)
    sql = match.group(1).strip() if match else raw.strip()

    if not sql.upper().startswith(("SELECT", "WITH", "SHOW", "DESCRIBE")):
        print(f"[warning] Response doesn't look like SQL:\n{sql}")

    return sql
