from flask import Flask, render_template, request, jsonify, session
import sqlite3
import hashlib
import joblib
import pandas as pd
from datetime import datetime
from functools import wraps

# =========================================================
# FLASK CONFIGURATION
# =========================================================

app = Flask(__name__)

# Demo/academic project secret key
app.secret_key = "agrismart-ai-academic-project-key"

DATABASE = "agrismart.db"
MODEL_FILE = "fertilizer_model.pkl"


# =========================================================
# LOAD MACHINE LEARNING MODEL
# =========================================================

try:
    model = joblib.load(MODEL_FILE)
    MODEL_LOADED = True
except Exception as e:
    model = None
    MODEL_LOADED = False
    print("Model loading error:", e)


# =========================================================
# FERTILIZER INFORMATION
# =========================================================

fertilizer_info = {

    "DAP": {
        "name": "DAP",
        "description": "Diammonium Phosphate is a commonly used phosphorus-containing fertilizer.",
        "grade": "Common grade: 18-46-0"
    },

    "Urea": {
        "name": "Urea",
        "description": "Urea is a nitrogen fertilizer commonly used to supply nitrogen to crops.",
        "grade": "Nitrogen fertilizer"
    },

    "14-35-14": {
        "name": "14-35-14",
        "description": "14-35-14 is a fertilizer class present in the project dataset.",
        "grade": "N-P₂O₅-K₂O notation"
    },

    "20-20": {
        "name": "20-20",
        "description": "20-20 is a fertilizer class present in the project dataset.",
        "grade": "Dataset fertilizer class"
    },

    "28-28": {
        "name": "28-28",
        "description": "28-28 is a fertilizer class present in the project dataset.",
        "grade": "Dataset fertilizer class"
    },

    "10-26-26": {
        "name": "10-26-26",
        "description": "10-26-26 is a fertilizer class present in the project dataset.",
        "grade": "N-P₂O₅-K₂O notation"
    },

    "17-17-17": {
        "name": "17-17-17",
        "description": "17-17-17 is a fertilizer class present in the project dataset.",
        "grade": "N-P₂O₅-K₂O notation"
    }
}


# =========================================================
# DATABASE
# =========================================================

def get_db():
    connection = sqlite3.connect(DATABASE)
    connection.row_factory = sqlite3.Row
    return connection


def initialize_database():

    connection = get_db()
    cursor = connection.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS predictions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,

            temperature REAL NOT NULL,
            humidity REAL NOT NULL,
            moisture REAL NOT NULL,

            soil_type TEXT NOT NULL,
            crop_type TEXT NOT NULL,

            nitrogen REAL NOT NULL,
            potassium REAL NOT NULL,
            phosphorus REAL NOT NULL,

            fertilizer TEXT NOT NULL,
            created_at TEXT NOT NULL,

            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    """)

    connection.commit()
    connection.close()


initialize_database()


# =========================================================
# PASSWORD HASHING
# =========================================================

def hash_password(password):
    return hashlib.sha256(
        password.encode("utf-8")
    ).hexdigest()


# =========================================================
# LOGIN REQUIRED DECORATOR
# =========================================================

def login_required(function):

    @wraps(function)
    def wrapper(*args, **kwargs):

        if "user_id" not in session:
            return jsonify({
                "success": False,
                "message": "Please login first."
            }), 401

        return function(*args, **kwargs)

    return wrapper


# =========================================================
# MAIN PAGE
# =========================================================

@app.route("/")
def home():
    return render_template("index.html")


# =========================================================
# SIGN UP
# =========================================================

@app.route("/api/signup", methods=["POST"])
def signup():

    data = request.get_json()

    name = data.get("name", "").strip()
    username = data.get("username", "").strip()
    password = data.get("password", "")

    if not name or not username or not password:

        return jsonify({
            "success": False,
            "message": "Please fill all fields."
        }), 400

    if len(password) < 4:

        return jsonify({
            "success": False,
            "message": "Password must contain at least 4 characters."
        }), 400

    connection = get_db()
    cursor = connection.cursor()

    try:

        cursor.execute("""
            INSERT INTO users
            (name, username, password, created_at)
            VALUES (?, ?, ?, ?)
        """, (
            name,
            username,
            hash_password(password),
            datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ))

        connection.commit()

        user_id = cursor.lastrowid

        session["user_id"] = user_id
        session["name"] = name
        session["username"] = username

        return jsonify({
            "success": True,
            "message": "Account created successfully.",
            "user": {
                "name": name,
                "username": username
            }
        })

    except sqlite3.IntegrityError:

        return jsonify({
            "success": False,
            "message": "Username already exists."
        }), 409

    finally:

        connection.close()


# =========================================================
# LOGIN
# =========================================================

@app.route("/api/login", methods=["POST"])
def login():

    data = request.get_json()

    username = data.get("username", "").strip()
    password = data.get("password", "")

    if not username or not password:

        return jsonify({
            "success": False,
            "message": "Please enter username and password."
        }), 400

    connection = get_db()

    user = connection.execute("""
        SELECT *
        FROM users
        WHERE username = ?
        AND password = ?
    """, (
        username,
        hash_password(password)
    )).fetchone()

    connection.close()

    if user is None:

        return jsonify({
            "success": False,
            "message": "Invalid username or password."
        }), 401

    session["user_id"] = user["id"]
    session["name"] = user["name"]
    session["username"] = user["username"]

    return jsonify({
        "success": True,
        "message": "Login successful.",
        "user": {
            "name": user["name"],
            "username": user["username"]
        }
    })


# =========================================================
# LOGOUT
# =========================================================

@app.route("/api/logout", methods=["POST"])
def logout():

    session.clear()

    return jsonify({
        "success": True,
        "message": "Logged out successfully."
    })


# =========================================================
# CURRENT USER
# =========================================================

@app.route("/api/me")
def current_user():

    if "user_id" not in session:

        return jsonify({
            "logged_in": False
        })

    connection = get_db()

    user = connection.execute("""
        SELECT id, name, username, created_at
        FROM users
        WHERE id = ?
    """, (
        session["user_id"],
    )).fetchone()

    connection.close()

    if user is None:

        session.clear()

        return jsonify({
            "logged_in": False
        })

    return jsonify({
        "logged_in": True,
        "user": {
            "id": user["id"],
            "name": user["name"],
            "username": user["username"],
            "created_at": user["created_at"]
        }
    })


# =========================================================
# MODEL INFORMATION
# =========================================================

@app.route("/api/stats")
def stats():

    fertilizer_classes = []

    if model is not None:

        try:
            fertilizer_classes = list(
                model.classes_
            )
        except Exception:
            fertilizer_classes = list(
                fertilizer_info.keys()
            )

    return jsonify({
        "model_loaded": MODEL_LOADED,
        "input_features": 8,
        "fertilizer_classes": len(fertilizer_classes)
    })


# =========================================================
# FERTILIZER PREDICTION
# =========================================================

@app.route("/api/predict", methods=["POST"])
@login_required
def predict():

    if model is None:

        return jsonify({
            "success": False,
            "message": "Machine learning model could not be loaded."
        }), 500

    data = request.get_json()

    try:

        temperature = float(data["temperature"])
        humidity = float(data["humidity"])
        moisture = float(data["moisture"])

        soil_type = data["soil_type"]
        crop_type = data["crop_type"]

        nitrogen = float(data["nitrogen"])
        potassium = float(data["potassium"])
        phosphorus = float(data["phosphorus"])

    except (KeyError, ValueError, TypeError):

        return jsonify({
            "success": False,
            "message": "Please enter valid agricultural values."
        }), 400


    # -----------------------------------------------------
    # INPUT VALIDATION
    # -----------------------------------------------------

    if not 0 <= temperature <= 60:

        return jsonify({
            "success": False,
            "message": "Temperature must be between 0 and 60 °C."
        }), 400

    if not 0 <= humidity <= 100:

        return jsonify({
            "success": False,
            "message": "Humidity must be between 0 and 100%."
        }), 400

    if not 0 <= moisture <= 100:

        return jsonify({
            "success": False,
            "message": "Soil moisture must be between 0 and 100%."
        }), 400

    if nitrogen < 0 or potassium < 0 or phosphorus < 0:

        return jsonify({
            "success": False,
            "message": "Nutrient values cannot be negative."
        }), 400


    # -----------------------------------------------------
    # CREATE DATAFRAME
    # -----------------------------------------------------

    input_data = pd.DataFrame([{

        "Temperature": temperature,

        "Humidity": humidity,

        "Moisture": moisture,

        "Soil Type": soil_type,

        "Crop Type": crop_type,

        "Nitrogen": nitrogen,

        "Potassium": potassium,

        "Phosphorus": phosphorus

    }])


    # -----------------------------------------------------
    # MODEL PREDICTION
    # -----------------------------------------------------

    prediction = model.predict(input_data)[0]

    prediction = str(prediction)


    # -----------------------------------------------------
    # SAVE PREDICTION HISTORY
    # -----------------------------------------------------

    connection = get_db()

    connection.execute("""
        INSERT INTO predictions
        (
            user_id,
            temperature,
            humidity,
            moisture,
            soil_type,
            crop_type,
            nitrogen,
            potassium,
            phosphorus,
            fertilizer,
            created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (

        session["user_id"],

        temperature,
        humidity,
        moisture,

        soil_type,
        crop_type,

        nitrogen,
        potassium,
        phosphorus,

        prediction,

        datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S"
        )
    ))

    connection.commit()
    connection.close()


    info = fertilizer_info.get(
        prediction,
        {
            "name": prediction,
            "description": "This fertilizer class is available in the project dataset.",
            "grade": "Project dataset class"
        }
    )


    return jsonify({

        "success": True,

        "prediction": prediction,

        "info": info,

        "inputs": {

            "temperature": temperature,

            "humidity": humidity,

            "moisture": moisture,

            "soil_type": soil_type,

            "crop_type": crop_type,

            "nitrogen": nitrogen,

            "potassium": potassium,

            "phosphorus": phosphorus

        }

    })


# =========================================================
# PREDICTION HISTORY
# =========================================================

@app.route("/api/history")
@login_required
def history():

    connection = get_db()

    rows = connection.execute("""
        SELECT *
        FROM predictions
        WHERE user_id = ?
        ORDER BY id DESC
    """, (
        session["user_id"],
    )).fetchall()

    connection.close()

    history_data = []

    for row in rows:

        history_data.append({

            "id": row["id"],

            "temperature": row["temperature"],

            "humidity": row["humidity"],

            "moisture": row["moisture"],

            "soil_type": row["soil_type"],

            "crop_type": row["crop_type"],

            "nitrogen": row["nitrogen"],

            "potassium": row["potassium"],

            "phosphorus": row["phosphorus"],

            "fertilizer": row["fertilizer"],

            "created_at": row["created_at"]

        })

    return jsonify({
        "success": True,
        "history": history_data
    })


# =========================================================
# PROFILE
# =========================================================

@app.route("/api/profile")
@login_required
def profile():

    connection = get_db()

    user = connection.execute("""
        SELECT id, name, username, created_at
        FROM users
        WHERE id = ?
    """, (
        session["user_id"],
    )).fetchone()

    count = connection.execute("""
        SELECT COUNT(*)
        FROM predictions
        WHERE user_id = ?
    """, (
        session["user_id"],
    )).fetchone()[0]

    connection.close()

    return jsonify({

        "success": True,

        "profile": {

            "name": user["name"],

            "username": user["username"],

            "created_at": user["created_at"],

            "prediction_count": count

        }

    })


# =========================================================
# RUN APPLICATION
# =========================================================

if __name__ == "__main__":

    app.run(
        debug=True,
        host="127.0.0.1",
        port=5000
    )