import joblib
import pandas as pd

# Load trained model
model = joblib.load("fertilizer_model.pkl")

# User input
data = pd.DataFrame([{
    "Temperature": 26,
    "Humidity": 60,
    "Moisture": 40,
    "Soil Type": "Sandy",
    "Crop Type": "Rice",
    "Nitrogen": 40,
    "Potassium": 20,
    "Phosphorus": 30
}])

# Predict fertilizer
prediction = model.predict(data)

print("Recommended Fertilizer:", prediction[0])