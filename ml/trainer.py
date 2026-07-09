import joblib
import pandas as pd

from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder

from features import load_dataset


# -------------------------
# Load Dataset
# -------------------------

df = load_dataset()

# Convert PASS/FAIL into numbers
df["status"] = df["status"].map({
    "PASS": 0,
    "FAIL": 1
})

# Features
X = df[
    [
        "module",
        "browser",
        "environment",
        "priority",
        "execution_time"
    ]
]

# Target
y = df["status"]


# -------------------------
# Preprocessing
# -------------------------

categorical_features = [
    "module",
    "browser",
    "environment"
]

numeric_features = [
    "priority",
    "execution_time"
]

preprocessor = ColumnTransformer(

    transformers=[

        (
            "cat",
            OneHotEncoder(handle_unknown="ignore"),
            categorical_features
        ),

        (
            "num",
            "passthrough",
            numeric_features
        )

    ]

)


# -------------------------
# Model
# -------------------------

model = Pipeline(

    steps=[

        ("preprocessor", preprocessor),

        ("classifier",
         RandomForestClassifier(
             n_estimators=100,
             random_state=42
         )
        )

    ]

)


# -------------------------
# Train
# -------------------------

model.fit(X, y)

joblib.dump(model, "ml/model.pkl")

print("\nModel trained successfully!")
print("Saved as ml/model.pkl")