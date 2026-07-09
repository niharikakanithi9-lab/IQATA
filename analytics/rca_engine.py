def analyze_failure(failure_reason):

    if failure_reason is None:
        return "No Failure"


    failure_reason = failure_reason.lower()


    if "timeout" in failure_reason:
        return "Possible Cause: Slow Network or Server Response"


    elif "element" in failure_reason:
        return "Possible Cause: UI Element Changed"


    elif "assertion" in failure_reason:
        return "Possible Cause: Application Logic Error"


    elif "database" in failure_reason:
        return "Possible Cause: Database Connectivity Issue"


    elif "api" in failure_reason:
        return "Possible Cause: API Service Failure"


    elif "credential" in failure_reason:
        return "Possible Cause: Authentication Issue"


    else:
        return "Possible Cause: Unknown"


if __name__ == "__main__":

    reasons = [
        "Timeout",
        "Element Not Found",
        "Database Connection Lost",
        "API Failure"
    ]


    print("\n========== RCA ENGINE ==========")

    for reason in reasons:

        print("\nFailure:", reason)
        print(analyze_failure(reason))