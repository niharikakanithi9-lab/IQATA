import random
from faker import Faker

fake = Faker()

MODULES = [
    "Authentication",
    "Search",
    "Checkout",
    "Payment",
    "Profile",
    "Cart",
    "Orders",
    "Reports",
    "Settings",
    "Notifications"
]

BROWSERS = [
    "Chrome",
    "Firefox",
    "Edge"
]

ENVIRONMENTS = [
    "Development",
    "Staging",
    "Production"
]

FAILURE_REASONS = [
    "Element Not Found",
    "Timeout",
    "Assertion Failed",
    "Network Error",
    "Database Connection Lost",
    "Invalid Credentials",
    "API Failure",
    "Unknown Error"
]


def generate_test_cases(count=50):
    test_cases = []

    for i in range(1, count + 1):
        test_cases.append({
            "name": f"TC_{i:03}",
            "module": random.choice(MODULES),
            "browser": random.choice(BROWSERS),
            "environment": random.choice(ENVIRONMENTS),
            "priority": round(random.uniform(0.5, 1.0), 2),
            "active": 1
        })

    return test_cases


def generate_test_runs(test_case_count=50, runs=2000):

    test_runs = []

    for _ in range(runs):

        status = random.choices(
            ["PASS", "FAIL"],
            weights=[80, 20]
        )[0]

        failure = None

        if status == "FAIL":
            failure = random.choice(FAILURE_REASONS)

        test_runs.append({

            "test_case_id": random.randint(1, test_case_count),

            "status": status,

            "execution_time": round(random.uniform(0.5, 8.0), 2),

            "started_at": fake.date_time_this_year(),

            "ended_at": fake.date_time_this_year(),

            "failure_reason": failure,

            "suggested_root_cause": failure,

            "screenshot_url": f"screenshots/{fake.uuid4()}.png",

            "log_url": f"logs/{fake.uuid4()}.txt"

        })

    return test_runs