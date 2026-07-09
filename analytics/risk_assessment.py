import sqlite3


DB_NAME = "qa_platform.db"


def calculate_risk():

    conn = sqlite3.connect(DB_NAME)

    cursor = conn.cursor()


    cursor.execute("""
    SELECT
        tc.name,
        COUNT(tr.id),
        SUM(
            CASE 
            WHEN tr.status='FAIL' THEN 1
            ELSE 0
            END
        )

    FROM test_cases tc

    JOIN test_runs tr

    ON tc.id = tr.test_case_id

    GROUP BY tc.id

    """)


    results = cursor.fetchall()


    print("\n==============================")
    print(" QUALITY RISK ASSESSMENT")
    print("==============================")

    for name,total,failed in results:


        failure_rate = (failed/total)*100


        if failure_rate > 25:
            risk="HIGH"

        elif failure_rate > 10:
            risk="MEDIUM"

        else:
            risk="LOW"


        print(
            f"{name:<20} "
            f"Failure: {round(failure_rate,2)}% "
            f"Risk: {risk}"
        )


    conn.close()



if __name__=="__main__":
    calculate_risk()