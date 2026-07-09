import sqlite3
import pandas as pd

DB_NAME = "qa_platform.db"


def load_dataset():

    conn = sqlite3.connect(DB_NAME)

    query = """
    SELECT
        tc.module,
        tc.browser,
        tc.environment,
        tc.priority,
        tr.execution_time,
        tr.status
    FROM test_runs tr
    JOIN test_cases tc
    ON tr.test_case_id = tc.id
    """

    df = pd.read_sql_query(query, conn)

    conn.close()

    return df


if __name__ == "__main__":

    df = load_dataset()

    print(df.head())

    print("\nRows:", len(df))