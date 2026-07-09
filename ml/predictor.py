import joblib
import pandas as pd


# Load trained model
model = joblib.load("ml/model.pkl")


# Read test cases
test_cases = pd.read_csv(
    "data/test_cases.csv"
)


# Predict
predictions = model.predict(test_cases)

probabilities = model.predict_proba(test_cases)


# Add results
test_cases["prediction"] = predictions


test_cases["failure_probability"] = (
    probabilities[:,1] * 100
)


# Convert prediction
test_cases["prediction"] = test_cases["prediction"].map(
    {
        0:"LOW RISK - Likely Pass",
        1:"HIGH RISK - Likely Failure"
    }
)


print("\n==============================")
print("AI DEFECT PREDICTION")
print("==============================")

print(test_cases)


# Save results
test_cases.to_csv(
    "data/prediction_results.csv",
    index=False
)