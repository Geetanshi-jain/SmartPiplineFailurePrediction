# ============================================================
#   GIS PIPELINE — MODEL TRAINING
#   Dataset: corrected_gis_leakage_dataset.csv
#   1. Pressure Prediction  (Regression)
#   2. Leakage Prediction   (Classification)
# ============================================================

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import warnings
warnings.filterwarnings('ignore')

from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import (
    r2_score, mean_absolute_error, mean_squared_error,
    classification_report, roc_auc_score,
    confusion_matrix, ConfusionMatrixDisplay
)
import joblib

# ============================================================
# STEP 1 — LOAD DATASET
# ============================================================

# NOTE: Use corrected dataset — encoding + feature engineering already done
df = pd.read_csv('corrected_gis_leakage_dataset.csv')

print("=" * 55)
print("   DATASET INFO")
print("=" * 55)
print(f"Rows    : {df.shape[0]}")
print(f"Columns : {df.shape[1]}")
print(f"Columns : {df.columns.tolist()}")


# ============================================================
# PART 1 — PRESSURE PREDICTION (REGRESSION)
# ============================================================

print("\n" + "=" * 55)
print("   PART 1 : PRESSURE PREDICTION — REGRESSION")
print("=" * 55)

PRESSURE_FEATURES = [
    'Flow_Rate', 'Temperature', 'Vibration', 'RPM',
    'Operational_Hours', 'Latitude', 'Longitude',
    'Leakage_Flag',
    'Pressure_Flow_Ratio', 'Pressure_per_RPM',
    'Leakage_Risk_Score', 'Flow_x_Vibration',
    'Thermal_Stress', 'RPM_Vibration', 'Wear_Factor',
    'Zone_Enc', 'Block_Enc', 'Distance_from_Center'
]
# NOTE: Pressure_Zone_Deviation excluded — derived from Pressure (data leakage)

X_p = df[PRESSURE_FEATURES]
y_p = df['Pressure']

# Train-Test Split
X_p_train, X_p_test, y_p_train, y_p_test = train_test_split(
    X_p, y_p, test_size=0.2, random_state=42
)
print(f"\nTrain size : {X_p_train.shape[0]}")
print(f"Test  size : {X_p_test.shape[0]}")

# Model Training
pressure_model = RandomForestRegressor(
    n_estimators=100,
    random_state=42,
    n_jobs=-1
)
pressure_model.fit(X_p_train, y_p_train)
print("Pressure model trained!")

# Evaluation
y_p_pred = pressure_model.predict(X_p_test)
r2   = r2_score(y_p_test, y_p_pred)
mae  = mean_absolute_error(y_p_test, y_p_pred)
rmse = np.sqrt(mean_squared_error(y_p_test, y_p_pred))

print("\n--- Pressure Model Metrics ---")
print(f"R² Score : {r2:.4f}")
print(f"MAE      : {mae:.4f}")
print(f"RMSE     : {rmse:.4f}")

# Cross Validation
cv_r2 = cross_val_score(pressure_model, X_p, y_p, cv=5, scoring='r2')
print(f"\n5-Fold CV R² : {cv_r2.round(4)}")
print(f"Mean CV R²   : {cv_r2.mean():.4f} ± {cv_r2.std():.4f}")

# Feature Importance
p_imp = pd.Series(
    pressure_model.feature_importances_, index=PRESSURE_FEATURES
).sort_values(ascending=False)
print("\n--- Feature Importance (Pressure) ---")
print(p_imp.round(4))

# Plot
plt.figure(figsize=(12, 5))

plt.subplot(1, 2, 1)
plt.scatter(y_p_test, y_p_pred, alpha=0.4, color='steelblue', s=10)
plt.plot([y_p_test.min(), y_p_test.max()],
         [y_p_test.min(), y_p_test.max()], 'r--', lw=2)
plt.xlabel('Actual Pressure')
plt.ylabel('Predicted Pressure')
plt.title(f'Pressure: Actual vs Predicted\nR² = {r2:.4f}')

plt.subplot(1, 2, 2)
p_imp.head(10).plot(kind='barh', color='steelblue')
plt.xlabel('Importance')
plt.title('Top 10 Features — Pressure Prediction')
plt.gca().invert_yaxis()

plt.tight_layout()
plt.savefig('pressure_model_results.png', dpi=150)
plt.show()
print("Plot saved: pressure_model_results.png")

# Save Model
joblib.dump(pressure_model, 'pressure_model.pkl')
print("Model saved: pressure_model.pkl")


# ============================================================
# PART 2 — LEAKAGE PREDICTION (CLASSIFICATION)
# ============================================================

print("\n" + "=" * 55)
print("   PART 2 : LEAKAGE PREDICTION — CLASSIFICATION")
print("=" * 55)

print("\nClass Distribution:")
print(df['Leakage_Flag'].value_counts())
print(f"Leakage % : {df['Leakage_Flag'].mean() * 100:.1f}%  (imbalanced dataset)")

LEAKAGE_FEATURES = [
    'Pressure', 'Flow_Rate', 'Temperature', 'Vibration', 'RPM',
    'Operational_Hours', 'Latitude', 'Longitude',
    'Pressure_Flow_Ratio', 'Pressure_per_RPM',
    'Leakage_Risk_Score', 'Flow_x_Vibration',
    'Thermal_Stress', 'RPM_Vibration', 'Wear_Factor',
    'Zone_Enc', 'Block_Enc', 'Distance_from_Center'
]

X_l = df[LEAKAGE_FEATURES]
y_l = df['Leakage_Flag']

# Stratified Split — preserves leakage ratio in both sets
X_l_train, X_l_test, y_l_train, y_l_test = train_test_split(
    X_l, y_l, test_size=0.2, random_state=42, stratify=y_l
)
print(f"\nTrain size : {X_l_train.shape[0]}")
print(f"Test  size : {X_l_test.shape[0]}")

# Model Training — class_weight='balanced' handles imbalance
leakage_model = RandomForestClassifier(
    n_estimators=100,
    class_weight='balanced',
    random_state=42,
    n_jobs=-1
)
leakage_model.fit(X_l_train, y_l_train)
print("Leakage model trained!")

# Evaluation
y_l_pred  = leakage_model.predict(X_l_test)
y_l_proba = leakage_model.predict_proba(X_l_test)[:, 1]

print("\n--- Classification Report ---")
print(classification_report(y_l_test, y_l_pred,
                             target_names=['No Leakage', 'Leakage']))

auc = roc_auc_score(y_l_test, y_l_proba)
print(f"ROC-AUC Score : {auc:.4f}")

# Cross Validation
cv_auc = cross_val_score(leakage_model, X_l, y_l, cv=5, scoring='roc_auc')
print(f"\n5-Fold CV AUC : {cv_auc.round(4)}")
print(f"Mean CV AUC   : {cv_auc.mean():.4f} ± {cv_auc.std():.4f}")

# Feature Importance
l_imp = pd.Series(
    leakage_model.feature_importances_, index=LEAKAGE_FEATURES
).sort_values(ascending=False)
print("\n--- Feature Importance (Leakage) ---")
print(l_imp.round(4))

# Plot
plt.figure(figsize=(12, 5))

plt.subplot(1, 2, 1)
cm = confusion_matrix(y_l_test, y_l_pred)
ConfusionMatrixDisplay(cm, display_labels=['No Leakage', 'Leakage']).plot(
    ax=plt.gca(), colorbar=False, cmap='Blues'
)
plt.title(f'Confusion Matrix\nROC-AUC = {auc:.4f}')

plt.subplot(1, 2, 2)
l_imp.head(10).plot(kind='barh', color='tomato')
plt.xlabel('Importance')
plt.title('Top 10 Features — Leakage Prediction')
plt.gca().invert_yaxis()

plt.tight_layout()
plt.savefig('leakage_model_results.png', dpi=150)
plt.show()
print("Plot saved: leakage_model_results.png")

# Save Model
joblib.dump(leakage_model, 'leakage_model.pkl')
print("Model saved: leakage_model.pkl")


# ============================================================
# FINAL SUMMARY
# ============================================================

print("\n" + "=" * 55)
print("   FINAL SUMMARY")
print("=" * 55)
print(f"Pressure Prediction  →  R²      : {r2:.4f}")
print(f"                        MAE     : {mae:.4f}")
print(f"                        RMSE    : {rmse:.4f}")
print(f"Leakage  Prediction  →  ROC-AUC : {auc:.4f}")
print("=" * 55)
print("Models : pressure_model.pkl | leakage_model.pkl")
print("Plots  : pressure_model_results.png | leakage_model_results.png")
