from dotenv import load_dotenv
load_dotenv()

from tabulate import tabulate
from agent import get_sql
from db import get_session, run_query


def main():
    print("Connecting to Starburst...")
    session = get_session()
    print("Connected. Type your question (or 'exit' to quit).\n")

    while True:
        try:
            question = input("Question: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nBye!")
            break

        if not question:
            continue
        if question.lower() == "exit":
            print("Bye!")
            break

        print("Generating SQL...")
        sql = get_sql(question)
        print(f"\nSQL:\n{sql}\n")

        try:
            columns, rows = run_query(session, sql)
            if rows:
                print(tabulate(rows, headers=columns, tablefmt="psql"))
            else:
                print("(no rows returned)")
        except Exception as e:
            print(f"[error] Query failed: {e}")

        print()


if __name__ == "__main__":
    main()
