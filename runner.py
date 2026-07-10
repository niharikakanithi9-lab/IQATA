"""
runner.py

Executes the Selenium test suite.

Fixes applied:
  - url/browser/environment from the dashboard are read via argparse
    and now genuinely reach each test class, because the test classes'
    __init__ accepts them (see tests/base_test.py). Previously
    build_test_instance's first attempt raised TypeError (the test
    classes didn't accept those kwargs) and silently fell back to a
    no-arg constructor, so the URL field on the dashboard did nothing.
  - failure_reason is the real exception message, not always None.
  - screenshots are captured by the test itself, before its own
    teardown() quits the driver, and the path is read back here
    instead of being re-attempted on an already-closed session.
  - writes a per-test log file and stores its path.

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
    Now that tests/base_test.py's __init__ actually accepts
    url/browser/environment, this succeeds on the first try. The
    fallbacks are kept only as defensive guards in case a test class
    is ever added that hasn't been updated to accept these kwargs —
    they should no longer be the common path.
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
    Each test now takes its own screenshot (via self.capture_screenshot())
    BEFORE its own `finally: self.teardown()` quits the driver, and stores
    the path on self.screenshot_path.

    The old version tried to call driver.save_screenshot() from here in
    runner.py — but by the time run_test() returns, the test's own
    teardown() has already called driver.quit(), so the session is dead
    and save_screenshot() always raised (silently, caught by a bare
    except). Screenshots never actually saved. This just reads back the
    path the test already captured instead of re-attempting it on a
    closed session.
    """
    return getattr(test_instance, "screenshot_path", None)


def write_log(test_name, status, execution_time, failure_reason=None):
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

    modules_to_run = [m for m in requested_modules if m in AVAILABLE_TESTS]
    unknown_modules = [m for m in requested_modules if m not in AVAILABLE_TESTS]
    for m in unknown_modules:
        print(f"WARNING: no test class registered for module '{m}' — skipping.")

    if not modules_to_run:
        print("No valid modules selected. Nothing to run.")
        sys.exit(1)

    print(f"Target URL     : {website or '(none provided — tests use their own default URL)'}")
    print(f"Browser        : {browser}")
    print(f"Environment    : {environment}")
    print(f"Modules to run : {', '.join(modules_to_run)}")
    if website:
        print(
            "NOTE: Search and Checkout tests use hardcoded element IDs from "
            "saucedemo.com (e.g. #user-name, .inventory_item). Pointing them "
            "at an arbitrary custom URL will likely fail unless that site "
            "happens to use the same element structure."
        )

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
                None,
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
    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()