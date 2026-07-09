from database.sqlite_db import SQLiteDB


class Metrics:

    def __init__(self):
        self.db = SQLiteDB()
        self.db.connect()

    def total_test_cases(self):
        return self.db.fetchone(
            "SELECT COUNT(*) FROM test_cases"
        )[0]

    def total_test_runs(self):
        return self.db.fetchone(
            "SELECT COUNT(*) FROM test_runs"
        )[0]

    def passed_tests(self):
        return self.db.fetchone(
            "SELECT COUNT(*) FROM test_runs WHERE status='PASS'"
        )[0]

    def failed_tests(self):
        return self.db.fetchone(
            "SELECT COUNT(*) FROM test_runs WHERE status='FAIL'"
        )[0]

    def pass_rate(self):
        total = self.total_test_runs()

        if total == 0:
            return 0

        return round((self.passed_tests() / total) * 100, 2)

    def failure_rate(self):
        total = self.total_test_runs()

        if total == 0:
            return 0

        return round((self.failed_tests() / total) * 100, 2)

    def average_execution_time(self):
        avg = self.db.fetchone(
            "SELECT AVG(execution_time) FROM test_runs"
        )[0]

        if avg is None:
            return 0

        return round(avg, 2)

    def browser_statistics(self):
        return self.db.fetchall(
            """
            SELECT browser, COUNT(*)
            FROM test_cases
            GROUP BY browser
            """
        )

    def environment_statistics(self):
        return self.db.fetchall(
            """
            SELECT environment, COUNT(*)
            FROM test_cases
            GROUP BY environment
            """
        )

    def module_statistics(self):
        return self.db.fetchall(
            """
            SELECT module, COUNT(*)
            FROM test_cases
            GROUP BY module
            """
        )

    def close(self):
        self.db.close()


if __name__ == "__main__":

    metrics = Metrics()

    print("\n========== QA METRICS ==========\n")

    print("Total Test Cases       :", metrics.total_test_cases())
    print("Total Test Runs        :", metrics.total_test_runs())
    print("Passed Tests           :", metrics.passed_tests())
    print("Failed Tests           :", metrics.failed_tests())
    print("Pass Rate              :", metrics.pass_rate(), "%")
    print("Failure Rate           :", metrics.failure_rate(), "%")
    print("Average Execution Time :", metrics.average_execution_time(), "sec")

    print("\nBrowser Statistics")
    for browser in metrics.browser_statistics():
        print(browser)

    print("\nEnvironment Statistics")
    for env in metrics.environment_statistics():
        print(env)

    print("\nModule Statistics")
    for module in metrics.module_statistics():
        print(module)

    metrics.close()