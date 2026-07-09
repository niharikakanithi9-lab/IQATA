import sqlite3

DB_NAME = "qa_platform.db"


def calculate_priority():

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            tc.id,
            tc.name,
            tc.priority,
            COUNT(tr.id) AS total_runs,
            SUM(CASE WHEN tr.status='FAIL' THEN 1 ELSE 0 END) AS failures,
            AVG(tr.execution_time) AS avg_time
        FROM test_cases tc
        LEFT JOIN test_runs tr
            ON tc.id = tr.test_case_id
        GROUP BY tc.id
    """)

    rows = cursor.fetchall()

    priorities = []

    for row in rows:

        test_id = row[0]
        name = row[1]
        base_priority = row[2]
        total_runs = row[3] or 0
        failures = row[4] or 0
        avg_time = row[5] or 0

        if total_runs == 0:
            failure_rate = 0
        else:
            failure_rate = failures / total_runs

        # AI-inspired Priority Score
        score = (
            (failure_rate * 0.5) +
            ((avg_time / 10) * 0.3) +
            (base_priority * 0.2)
        )

        priorities.append({
            "name": name,
            "failure_rate": round(failure_rate * 100, 2),
            "avg_time": round(avg_time, 2),
            "priority_score": round(score, 3)
        })

    conn.close()

    priorities.sort(
        key=lambda x: x["priority_score"],
        reverse=True
    )

    return priorities


def display_priorities():

    print("\n==============================")
    print(" AI TEST CASE PRIORITIZATION")
    print("==============================")

    priorities = calculate_priority()

    print(
        f"{'Rank':<5}"
        f"{'Test Case':<25}"
        f"{'Score':<10}"
        f"{'Failure %':<12}"
        f"{'Avg Time'}"
    )

    print("-" * 70)

    for rank, item in enumerate(priorities, start=1):

        print(
            f"{rank:<5}"
            f"{item['name']:<25}"
            f"{item['priority_score']:<10}"
            f"{item['failure_rate']:<12}"
            f"{item['avg_time']} sec"
        )


if __name__ == "__main__":
    display_priorities()