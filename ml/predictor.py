import joblib
import pandas as pd


# Load trained model
model = joblib.load("ml/model.pkl")


def predict_test_case(
    module,
    browser,
    environment,
    priority,
    execution_time
):

    test_data = pd.DataFrame(
        [
            {
                "module": module,
                "browser": browser,
                "environment": environment,
                "priority": priority,
                "execution_time": execution_time
            }
        ]
    )


    prediction = model.predict(test_data)

    probability = model.predict_proba(test_data)


    risk = probability[0][1] * 100


    if prediction[0] == 1:
        result = "HIGH RISK - Likely Failure"
    else:
        result = "LOW RISK - Likely Pass"


    print("\n==============================")
    print(" AI DEFECT PREDICTION")
    print("==============================")

    print("Module :", module)
    print("Browser :", browser)
    print("Environment :", environment)

    print("------------------------------")

    print("Prediction :", result)
    print("Failure Probability :", round(risk,2), "%")

    print("==============================")


if __name__ == "__main__":

    predict_test_case(
        module="Checkout",
        browser="Chrome",
        environment="Production",
        priority=0.95,
        execution_time=5.2
    )