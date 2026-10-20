import pandas as pd
import joblib

from sklearn.model_selection import train_test_split
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder
from sklearn.pipeline import Pipeline
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score


# 1. Load dataset
df = pd.read_csv("dataset/Fertilizer Prediction.csv")

# 2. Fix column names
df = df.rename(columns={
    "Temparature": "Temperature",
    "Phosphorous": "Phosphorus"
})

# 3. Input features
X = df[
    [
        "Temperature",
        "Humidity",
        "Moisture",
        "Soil Type",
        "Crop Type",
        "Nitrogen",
        "Potassium",
        "Phosphorus"
    ]
]

# 4. Target/output
y = df["Fertilizer Name"]

# 5. Categorical and numerical columns
categorical_features = ["Soil Type", "Crop Type"]

numerical_features = [
    "Temperature",
    "Humidity",
    "Moisture",
    "Nitrogen",
    "Potassium",
    "Phosphorus"
]

# 6. Preprocessing
preprocessor = ColumnTransformer(
    transformers=[
        ("categorical", OneHotEncoder(handle_unknown="ignore"), categorical_features),
        ("numerical", "passthrough", numerical_features)
    ]
)

# 7. Create ML model
model = RandomForestClassifier(
    n_estimators=100,
    random_state=42
)

# 8. Create pipeline
pipeline = Pipeline([
    ("preprocessor", preprocessor),
    ("model", model)
])

# 9. Split dataset
X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.2,
    random_state=42
)

# 10. Train model
pipeline.fit(X_train, y_train)

# 11. Test model
y_pred = pipeline.predict(X_test)

accuracy = accuracy_score(y_test, y_pred)

print("Model Training Completed!")
print("Accuracy:", accuracy)

# 12. Save trained model
joblib.dump(pipeline, "fertilizer_model.pkl")

print("Model saved as fertilizer_model.pkl")