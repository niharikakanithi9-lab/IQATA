from database.sqlite_db import SQLiteDB
from data.generator import generate_test_cases
from data.generator import generate_test_runs


db = SQLiteDB()
db.connect()


# -----------------------------
# Insert Test Cases
# -----------------------------

test_cases = generate_test_cases()

for tc in test_cases:

    db.execute(
        """
        INSERT INTO test_cases
        (name,module,browser,environment,priority,active)

        VALUES
        (?,?,?,?,?,?)
        """,

        (
            tc["name"],
            tc["module"],
            tc["browser"],
            tc["environment"],
            tc["priority"],
            tc["active"]
        )

    )


# -----------------------------
# Insert Test Runs
# -----------------------------

runs = generate_test_runs()

for run in runs:

    db.execute(
        """
        INSERT INTO test_runs
        (
        test_case_id,
        status,
        execution_time,
        started_at,
        ended_at,
        failure_reason,
        suggested_root_cause,
        screenshot_url,
        log_url
        )

        VALUES
        (?,?,?,?,?,?,?,?,?)
        """,

        (
            run["test_case_id"],
            run["status"],
            run["execution_time"],
            run["started_at"],
            run["ended_at"],
            run["failure_reason"],
            run["suggested_root_cause"],
            run["screenshot_url"],
            run["log_url"]
        )

    )


print("Database seeded successfully!")

db.close()