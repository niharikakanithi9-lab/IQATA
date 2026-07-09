import sqlite3


DB="qa_platform.db"


def coverage_analysis():

    conn=sqlite3.connect(DB)

    cursor=conn.cursor()


    cursor.execute("""
    SELECT
    module,
    COUNT(*)

    FROM test_cases

    GROUP BY module
    """)


    results=cursor.fetchall()


    print("\n==============================")
    print(" TEST COVERAGE ANALYSIS")
    print("==============================")


    total=0


    for module,count in results:

        total+=count

        print(
            f"{module:<20} Tests: {count}"
        )


    print("------------------------------")
    print("Total Covered Tests:",total)


    conn.close()



if __name__=="__main__":
    coverage_analysis()