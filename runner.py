"""
runner.py

Executes the Selenium test suite.

Fixes applied (see review notes):
  - Problem 2: reads website/browser/environment/modules from the
    command line instead of ignoring them.
  - Problem 3 & 4: passes the URL and browser choice into each test
    class instead of letting the test decide on its own.
  - Problem 5: only runs the modules that were actually selected.
  - Problem 6: stores the real exception (TimeoutException,
    NoSuchElementException, AssertionError, etc.) as failure_reason
    instead of always inserting None.
  - Problem 7: saves a screenshot on failure (if the test exposes a
    Selenium `driver`) and stores its path.
  - Problem 8: writes a per-test log file and stores its path.

Usage:
    python runner.py --url https://example.com --browser Chrome \
        --env Production --modules Login,Search,Checkout
"""

import argparse
import os
import sys
import time
from datetime import datetime

from database.sqlite_db import SQLiteDB

# ------------------------------------------------------------------
# Registry of available test modules. Each entry maps the "module
# name" used by the dashboard's checkboxes to the class that
# implements it. Registration/Profile are optional: if those test
# files don't exist yet, runner.py still runs fine and just reports
# that the module isn't available instead of crashing.
# ------------------------------------------------------------------
AVAILABLE_TESTS = {}

from tests.login_test import LoginTest
AVAILABLE_TESTS["Login"] = LoginTest

from tests.search_test import SearchTest
AVAILABLE_TESTS["Search"] = SearchTest

from tests.checkout_test import CheckoutTest
AVAILABLE_TESTS["Checkout"] = CheckoutTest




def parse_args():
    parser = argparse.ArgumentParser(description="Run the Selenium test suite.")
    parser.add_argument("--url", default=None, help="Website URL under test")
    parser.add_argument("--browser", default="Chrome", help="Chrome / Firefox / Edge")
    parser.add_argument("--env", default="Development", help="Development / Staging / Production")
    parser.add_argument(
        "--modules",
        default="Login,Search,Checkout",
        help="Comma-separated module names, e.g. Login,Search,Checkout",
    )
    return parser.parse_args()


def build_test_instance(test_cls, url, browser, environment):
    """
    Instantiate a test class, passing url/browser/environment through
    so the dropdown/URL box on the dashboard actually changes what
    Selenium does (Problems 3 & 4).

    Falls back to a plain no-arg constructor if the test class hasn't
    been updated yet to accept these kwargs or positional args, so
    this keeps working incrementally rather than requiring every test
    file to change at once.
    """
    try:
        return test_cls(url=url, browser=browser, environment=environment)
    except TypeError:
        pass
    try:
        return test_cls(url, browser, environment)
    except TypeError:
        pass
    return test_cls()


def capture_screenshot(test_instance, test_name):
    """
    Save a screenshot if the test instance exposes a Selenium
    `driver` attribute. Returns None (not a fake path) if no driver
    is available, so the DB only ever holds real paths (Problem 7).
    """
    driver = getattr(test_instance, "driver", None)
    if driver is None:
        return None

    os.makedirs("screenshots", exist_ok=True)
    safe_name = test_name.lower().replace(" ", "_")
    path = f"screenshots/{safe_name}_{int(time.time())}.png"
    try:
        driver.save_screenshot(path)
        return path
    except Exception:
        return None


def write_log(test_name, status, execution_time, failure_reason=None):
    """
    Write a per-test log file and return its path (Problem 8).
    """
    os.makedirs("logs", exist_ok=True)
    safe_name = test_name.lower().replace(" ", "_")
    path = f"logs/{safe_name}_{int(time.time())}.log"

    with open(path, "w") as f:
        f.write(f"Test          : {test_name}\n")
        f.write(f"Status        : {status}\n")
        f.write(f"Execution time: {execution_time} sec\n")
        f.write(f"Timestamp     : {datetime.now()}\n")
        if failure_reason:
            f.write("-" * 40 + "\n")
            f.write(f"Failure reason: {failure_reason}\n")

    return path


def main():
    args = parse_args()

    website = args.url
    browser = args.browser
    environment = args.env
    requested_modules = [m.strip() for m in args.modules.split(",") if m.strip()]

    # Problem 5: only run what was actually selected.
    modules_to_run = [m for m in requested_modules if m in AVAILABLE_TESTS]
    unknown_modules = [m for m in requested_modules if m not in AVAILABLE_TESTS]
    for m in unknown_modules:
        print(f"WARNING: no test class registered for module '{m}' — skipping.")

    if not modules_to_run:
        print("No valid modules selected. Nothing to run.")
        sys.exit(1)

    print(f"Target URL     : {website or '(none provided)'}")
    print(f"Browser        : {browser}")
    print(f"Environment    : {environment}")
    print(f"Modules to run : {', '.join(modules_to_run)}")

    db = SQLiteDB()
    db.connect()

    passed = 0
    failed = 0
    latest_results = []

    for index, module_name in enumerate(modules_to_run, start=1):
        test_cls = AVAILABLE_TESTS[module_name]
        display_name = f"{module_name} Test"

        print(f"\nRunning {display_name}...")
        test_instance = build_test_instance(test_cls, website, browser, environment)

        start = time.time()
        failure_reason = None
        status = False

        try:
            status = test_instance.run_test()
        except Exception as e:
            # Problem 6: store the real exception instead of None.
            status = False
            failure_reason = f"{type(e).__name__}: {e}"

        end = time.time()
        execution_time = round(end - start, 2)
        result = "PASS" if status else "FAIL"

        if not status and failure_reason is None:
            failure_reason = "Test reported FAIL without raising an exception."

        screenshot_url = capture_screenshot(test_instance, display_name) if not status else None
        log_url = write_log(display_name, result, execution_time, failure_reason)

        latest_results.append((display_name, result, execution_time))

        if status:
            passed += 1
        else:
            failed += 1

        print(f"{display_name}: {result} ({execution_time} sec)")
        if failure_reason:
            print(f"  Failure reason: {failure_reason}")

        db.execute(
            """
            INSERT INTO test_runs (
                test_case_id, status, execution_time,
                started_at, ended_at,
                failure_reason, suggested_root_cause,
                screenshot_url, log_url
            ) VALUES (?,?,?,?,?,?,?,?,?)
            """,
            (
                index,
                result,
                execution_time,
                datetime.now(),
                datetime.now(),
                failure_reason,
                None,  # RCA suggestion is computed on-demand by rca_engine.py
                screenshot_url,
                log_url,
            ),
        )

    print("\n==============================")
    print("TOTAL TESTS :", len(modules_to_run))
    print("PASSED :", passed)
    print("FAILED :", failed)
    print("\nLATEST LIVE EXECUTIONS")
    print("-" * 40)
    for name, result, exec_time in latest_results:
        print(f"{name:<20} {result:<6} {exec_time} sec")
    print("==============================")

    db.close()

    # Non-zero exit code on any failure so app.py's
    # `result.returncode == 0` success check is meaningful.
    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()