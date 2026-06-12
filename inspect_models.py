import joblib
import pandas as pd

try:
    pressure_model = joblib.load('pressure_model.pkl')
    print("--- Pressure Model ---")
    print(f"Type: {type(pressure_model)}")
    if hasattr(pressure_model, 'n_features_in_'):
        print(f"n_features_in_: {pressure_model.n_features_in_}")
    if hasattr(pressure_model, 'feature_names_in_'):
        print(f"feature_names_in_: {pressure_model.feature_names_in_}")
except Exception as e:
    print(f"Error inspecting pressure model: {e}")

try:
    leakage_model = joblib.load('leakage_model.pkl')
    print("\n--- Leakage Model ---")
    print(f"Type: {type(leakage_model)}")
    if hasattr(leakage_model, 'n_features_in_'):
        print(f"n_features_in_: {leakage_model.n_features_in_}")
    if hasattr(leakage_model, 'feature_names_in_'):
        print(f"feature_names_in_: {leakage_model.feature_names_in_}")
except Exception as e:
    print(f"Error inspecting leakage model: {e}")
