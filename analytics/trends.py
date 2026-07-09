import sqlite3


DB="qa_platform.db"


def execution_trend():

    conn=sqlite3.connect(DB)

    cursor=conn.cursor()


    cursor.execute("""
    SELECT
    DATE(started_at),
    COUNT(*),
    SUM(
    CASE WHEN status='FAIL'
    THEN 1
    ELSE 0 END
    )

    FROM test_runs

    GROUP BY DATE(started_at)

    ORDER BY DATE(started_at)

    """)


    rows=cursor.fetchall()


    print("\n==============================")
    print(" QUALITY TREND ANALYSIS")
    print("==============================")


    for date,total,failed in rows:

        rate=(failed/total)*100

        print(
        date,
        "Runs:",
        total,
        "Failure:",
        round(rate,2),
        "%"
        )


    conn.close()



if __name__=="__main__":
    execution_trend()