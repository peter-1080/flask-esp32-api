import pandas as pd
import numpy as np
import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout
from sklearn.preprocessing import MinMaxScaler
import joblib
import os

# Load dataset
df = pd.read_csv("pondsEdited.csv")

# Convert Date column to datetime format
df["Date"] = pd.to_datetime(df["Date"], format="%d-%m-%Y %H:%M")

# Drop rows with missing values
df = df.dropna()

# Sort by date
df = df.sort_values(by="Date")

# Define target parameters
parameters = ["TEMP", "PH", "AMMONIA", "DO", "TURBIDITY"]

# Scale data
scalers = {}
for param in parameters:
    scalers[param] = MinMaxScaler()
    df[param] = scalers[param].fit_transform(df[[param]])

# Save scalers for later use
joblib.dump(scalers, "scalers.pkl")

# Function to create sequences for LSTM
def create_sequences(data, target, time_steps):
    X, y = [], []
    for i in range(len(data) - time_steps):
        X.append(data[i:i+time_steps])
        y.append(target[i+time_steps])
    return np.array(X), np.array(y)

# Prepare data for training
TIME_STEPS_6HR = 18  # 18 data points (~6 hours)
TIME_STEPS_12HR = 36  # 36 data points (~12 hours)
X_6hr, y_6hr = create_sequences(df[parameters].values, df[parameters].values, TIME_STEPS_6HR)
X_12hr, y_12hr = create_sequences(df[parameters].values, df[parameters].values, TIME_STEPS_12HR)

# Split data into train & test
train_size = int(0.8 * len(X_6hr))
X_train_6hr, X_test_6hr = X_6hr[:train_size], X_6hr[train_size:]
y_train_6hr, y_test_6hr = y_6hr[:train_size], y_6hr[train_size:]

train_size_12hr = int(0.8 * len(X_12hr))
X_train_12hr, X_test_12hr = X_12hr[:train_size_12hr], X_12hr[train_size_12hr:]
y_train_12hr, y_test_12hr = y_12hr[:train_size_12hr], y_12hr[train_size_12hr:]

# Define LSTM model
def build_lstm_model(input_shape):
    model = Sequential([
        LSTM(64, return_sequences=True, input_shape=input_shape),
        Dropout(0.2),
        LSTM(32, return_sequences=False),
        Dropout(0.2),
        Dense(len(parameters))  # Output layer with one neuron per parameter
    ])
    model.compile(optimizer='adam', loss='mse')
    return model

# Train models for 6hr & 12hr predictions
if not os.path.exists("lstm_6hr.h5"):
    print("Training 6-hour prediction model...")
    lstm_6hr = build_lstm_model((TIME_STEPS_6HR, len(parameters)))
    lstm_6hr.fit(X_train_6hr, y_train_6hr, epochs=50, batch_size=16, validation_data=(X_test_6hr, y_test_6hr))
    lstm_6hr.save("lstm_6hr.h5")
    print("6-hour model saved.")
else:
    print("Skipping 6-hour model training. Model already exists.")

if not os.path.exists("lstm_12hr.h5"):
    print("Training 12-hour prediction model...")
    lstm_12hr = build_lstm_model((TIME_STEPS_12HR, len(parameters)))
    lstm_12hr.fit(X_train_12hr, y_train_12hr, epochs=50, batch_size=16, validation_data=(X_test_12hr, y_test_12hr))
    lstm_12hr.save("lstm_12hr.h5")
    print("12-hour model saved.")
else:
    print("Skipping 12-hour model training. Model already exists.")

print("Training complete. Models saved!")
