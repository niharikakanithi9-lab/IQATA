"""
runner.py

Executes the Selenium test suite.
"""

import argparse
import os
import sys
import time
from datetime import datetime

from database.azure_sql import AzureSQL
from config import AZURE_SQL_CONNECTION


AVAILABLE_TESTS = {}

from tests.login_test import LoginTest
AVAILABLE_TESTS["Login"] = LoginTest

from tests.search_test import SearchTest
AVAILABLE_TESTS["Search"] = SearchTest

from tests.checkout_test import CheckoutTest
AVAILABLE_TESTS["Checkout"] = CheckoutTest


def parse_args():
    parser = argparse.ArgumentParser(
        description="Run the Selenium test suite."
    )

    parser.add_argument(
        "--url",
        default="https://www.saucedemo.com/"
    )

    parser.add_argument(
        "--browser",
        default="Chrome"
    )

    parser.add_argument(
        "--env",
        default="Development"
    )

    parser.add_argument(
        "--modules",
        default="Login,Search,Checkout"
    )

    return parser.parse_args()



def build_test_instance(test_cls, url, browser, environment):

    try:
        return test_cls(
            url=url,
            browser=browser,
            environment=environment
        )

    except TypeError:
        return test_cls()



def capture_screenshot(test_instance):

    return getattr(
        test_instance,
        "screenshot_path",
        None
    )



def write_log(
        test_name,
        status,
        execution_time,
        failure_reason=None
):

    os.makedirs(
        "logs",
        exist_ok=True
    )

    filename = test_name.lower()

    path = (
        f"logs/{filename}_{int(time.time())}.log"
    )

    with open(path, "w") as f:

        f.write(
            f"Test : {test_name}\n"
        )

        f.write(
            f"Status : {status}\n"
        )

        f.write(
            f"Execution Time : {execution_time}\n"
        )

        f.write(
            f"Timestamp : {datetime.now()}\n"
        )

        if failure_reason:

            f.write(
                "\nFailure Reason:\n"
            )

            f.write(
                failure_reason
            )


    return path



def main():

    args = parse_args()


    website = args.url
    browser = args.browser
    environment = args.env


    modules_to_run = [
        m.strip()
        for m in args.modules.split(",")
        if m.strip() in AVAILABLE_TESTS
    ]


    print(
        f"Target URL : {website}"
    )

    print(
        f"Browser : {browser}"
    )

    print(
        f"Environment : {environment}"
    )

    print(
        f"Modules : {modules_to_run}"
    )


    # Azure SQL connection

    db = AzureSQL(
        AZURE_SQL_CONNECTION
    )

    db.connect()



    passed = 0
    failed = 0

    latest_results = []



    for module_name in modules_to_run:


        print(
            f"\nRunning {module_name} Test..."
        )


        test_class = AVAILABLE_TESTS[module_name]


        test = build_test_instance(
            test_class,
            website,
            browser,
            environment
        )


        start = time.time()


        failure_reason = None


        try:

            status = test.run_test()


        except Exception as e:

            status = False

            failure_reason = str(e)



        execution_time = round(
            time.time() - start,
            2
        )



        result = (
            "PASS"
            if status
            else
            "FAIL"
        )



        screenshot = None


        if not status:

            screenshot = capture_screenshot(
                test
            )



        log = write_log(
            module_name,
            result,
            execution_time,
            failure_reason
        )



        # Save result to Azure SQL

        row = db.fetchone(
            """
            SELECT id 
            FROM test_cases
            WHERE name = ?
            """,
            (
                f"{module_name} Test",
            )
        )



        if row:

            test_case_id = row[0]


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

                    test_case_id,

                    result,

                    execution_time,

                    datetime.now(),

                    datetime.now(),

                    failure_reason,

                    None,

                    screenshot,

                    log

                )

            )


        else:

            print(
                f"Test case missing: {module_name}"
            )



        latest_results.append(
            (
                module_name,
                result,
                execution_time
            )
        )



        if status:

            passed += 1

            print(
                f"{module_name}: PASS"
            )


        else:

            failed += 1

            print(
                f"{module_name}: FAIL"
            )



    print(
        "\n=============================="
    )

    print(
        "TOTAL :",
        len(modules_to_run)
    )

    print(
        "PASSED :",
        passed
    )

    print(
        "FAILED :",
        failed
    )


    print(
        "\nLatest Results"
    )


    for row in latest_results:

        print(row)


    print(
        "=============================="
    )


    db.close()


    sys.exit(
        0 if failed == 0 else 1
    )



if __name__ == "__main__":

    main()