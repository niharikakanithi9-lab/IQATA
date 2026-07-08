import time
from datetime import datetime

from database.sqlite_db import SQLiteDB

from tests.login_test import LoginTest
from tests.search_test import SearchTest
from tests.checkout_test import CheckoutTest


db = SQLiteDB()
db.connect()


tests = [

    ("Login Test", LoginTest()),

    ("Search Test", SearchTest()),

    ("Checkout Test", CheckoutTest())

]

passed = 0
failed = 0


for index, (name, test) in enumerate(tests, start=1):

    print(f"\nRunning {name}...")

    start = time.time()

    status = test.run_test()

    end = time.time()

    execution_time = round(end - start, 2)

    result = "PASS" if status else "FAIL"

    if status:
        passed += 1
    else:
        failed += 1

    print(f"{name}: {result} ({execution_time} sec)")

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

        VALUES (?,?,?,?,?,?,?,?,?)
        """,

        (
            index,
            result,
            execution_time,
            datetime.now(),
            datetime.now(),
            None,
            None,
            None,
            None
        )

    )

print("\n==============================")
print("TOTAL TESTS :", len(tests))
print("PASSED      :", passed)
print("FAILED      :", failed)
print("==============================")

db.close()