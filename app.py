from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import requests
import telebot
from datetime import datetime

app = Flask(__name__)
CORS(app)

# Store latest sensor data
latest_data = {}

# Telegram Bot Config
TELEGRAM_BOT_TOKEN = "7662400218:AAFm4HOnWKMhRGc624xPMAyczMk"  # Replace with your valid token
CHAT_ID = "868999324"
bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)

# Safe Ranges for Water Parameters
SAFE_RANGES = {
    "TEMP": (20, 30),
    "PH": (6.5, 8.5),
    "AMMONIA": (0, 0.5),
    "DO": (5, 10),
    "TURBIDITY": (0, 50)
}


# Send Telegram Alert
def send_telegram_alert(parameter, value, alert_type="Real-time"):
    message = f"⚠ ALERT: {parameter} ({alert_type}) is out of range! Current Value: {value}"
    bot.send_message(CHAT_ID, message)


# ✅ Route to receive data from ESP32 (Fixed to match ESP32 request)
@app.route('/update', methods=['POST'])
def update_data():
    global latest_data
    try:
        data = request.json
        if not data:
            return jsonify({"error": "Invalid JSON data"}), 400

        print("Received Data:", data)  # Debugging Log

        data["timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Check if real-time values are in safe range
        for key, (low, high) in SAFE_RANGES.items():
            if key in data and not (low <= data[key] <= high):
                send_telegram_alert(key, data[key], "Real-time")

        latest_data = data
        return jsonify({"message": "Data received", "data": latest_data}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# Route to get latest data
@app.route('/latest', methods=['GET'])
def get_latest_data():
    if not latest_data:
        return jsonify({"message": "No data available"})
    return jsonify(latest_data)


# Prediction API with Alerts
@app.route('/predict/<interval>', methods=['GET'])
def predict_data(interval):
    if interval not in ["6hr", "12hr"]:
        return jsonify({"error": "Invalid interval. Use '6hr' or '12hr'."})

    # Dummy prediction logic (Replace with ML model)
    prediction = {key: round(value * 1.1, 2) for key, value in latest_data.items() if isinstance(value, (int, float))}

    # Check if predictions are out of range
    for key, (low, high) in SAFE_RANGES.items():
        if key in prediction and not (low <= prediction[key] <= high):
            send_telegram_alert(key, prediction[key], f"{interval} Prediction")

    return jsonify({"interval": interval, "predictions": prediction})


# Route to serve the web UI
@app.route('/')
def home():
    return render_template('index.html')


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
