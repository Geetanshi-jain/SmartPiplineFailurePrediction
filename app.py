import os
import json
import math
import time
import threading
import random
import smtplib
import secrets
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from flask import Flask, jsonify, request, send_file
import pandas as pd
import numpy as np
import joblib

# ReportLab imports for summary-based PDF reports
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, KeepTogether
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

app = Flask(__name__, static_folder='static', static_url_path='/static')

# Set to store authenticated admin tokens
active_tokens = set()

def check_admin_auth():
    auth_header = request.headers.get('Authorization', '')
    if auth_header.startswith('Bearer '):
        token = auth_header.split(' ')[1]
        if token in active_tokens:
            return True
    return False


# File Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATASET_PATH = os.path.join(BASE_DIR, 'indore_pipeline_dataset.csv')
LEAKAGE_MODEL_PATH = os.path.join(BASE_DIR, 'leakage_model.pkl')
PRESSURE_MODEL_PATH = os.path.join(BASE_DIR, 'pressure_model.pkl')
CONFIG_PATH = os.path.join(BASE_DIR, 'config.json')

# Internal SMTP Configuration (hardcoded - not exposed to admin panel)
INTERNAL_SMTP_HOST = "smtp.gmail.com"
INTERNAL_SMTP_PORT = 587
MAIL_USE_TLS = True
MAIL_USE_SSL = False
INTERNAL_SMTP_USER = "geetanshijain300@gmail.com"
INTERNAL_SMTP_PASS = "yvmmysswkfixifja"
INTERNAL_SENDER_EMAIL = "geetanshijain300@gmail.com"

# Load Data and Models
df_pipes = None
leakage_model = None
pressure_model = None
live_alerts = []  # In-memory store for simulation alerts

# Global configuration lock
config_lock = threading.Lock()

def load_resources():
    global df_pipes, leakage_model, pressure_model
    try:
        if os.path.exists(DATASET_PATH):
            df_pipes = pd.read_csv(DATASET_PATH)
            print(f"[SUCCESS] Loaded dataset with {len(df_pipes)} records.")
        else:
            print(f"[ERROR] Dataset not found at: {DATASET_PATH}")
            
        if os.path.exists(LEAKAGE_MODEL_PATH):
            leakage_model = joblib.load(LEAKAGE_MODEL_PATH)
            print("[SUCCESS] Loaded leakage prediction model.")
        else:
            print(f"[ERROR] Leakage model not found at: {LEAKAGE_MODEL_PATH}")
            
        if os.path.exists(PRESSURE_MODEL_PATH):
            pressure_model = joblib.load(PRESSURE_MODEL_PATH)
            print("[SUCCESS] Loaded pressure prediction model.")
        else:
            print(f"[ERROR] Pressure model not found at: {PRESSURE_MODEL_PATH}")
    except Exception as e:
        print(f"[CRITICAL ERROR] Failed loading resources: {e}")

load_resources()

# Load/Save SMTP Configuration helper
def get_config():
    with config_lock:
        if os.path.exists(CONFIG_PATH):
            try:
                with open(CONFIG_PATH, 'r') as f:
                    cfg = json.load(f)
                    # Inject defaults if missing
                    if 'admin_username' not in cfg:
                        cfg['admin_username'] = 'admin'
                    if 'admin_password' not in cfg:
                        cfg['admin_password'] = 'admin123'
                    return cfg
            except Exception:
                pass
        return {
            "alert_email": "",
            "pressure_threshold_low": 45.0,
            "pressure_threshold_high": 75.0,
            "leak_prob_threshold": 0.70,
            "admin_username": "admin",
            "admin_password": "admin123"
        }

def save_config(cfg):
    with config_lock:
        try:
            with open(CONFIG_PATH, 'w') as f:
                json.dump(cfg, f, indent=4)
            return True
        except Exception as e:
            print(f"[ERROR] Failed to save config: {e}")
            return False

# Iterative solver for circular dependent predictions
def run_iterative_prediction(features_dict):
    """
    Predicts pressure and leakage probability using the two random forest models.
    """
    flow_rate = float(features_dict.get('Flow_Rate', 75.0))
    temp = float(features_dict.get('Temperature', 98.0))
    vib = float(features_dict.get('Vibration', 2.8))
    rpm = float(features_dict.get('RPM', 1800.0))
    hours = float(features_dict.get('Operational_Hours', 3000.0))
    lat = float(features_dict.get('Latitude', 22.7))
    lon = float(features_dict.get('Longitude', 75.8))
    
    zone_enc = int(features_dict.get('Zone_Enc', 3))
    block_enc = int(features_dict.get('Block_Enc', 1))
    
    # 1. Predict pressure using pressure_model (expects 9 features)
    p_inputs = [flow_rate, temp, vib, rpm, hours, lat, lon, zone_enc, block_enc]
    try:
        pressure_pred = float(pressure_model.predict([p_inputs])[0])
    except Exception as err:
        print(f"Pressure Model error: {err}")
        pressure_pred = 60.0
        
    # 2. Derive features for leakage_model (expects 18 features)
    dist_center = math.sqrt((lat - 22.677876)**2 + (lon - 75.808277)**2)
    wear_factor = hours * 0.00010002
    rpm_vib = rpm * vib
    flow_vib = flow_rate * vib
    
    pressure_flow_ratio = pressure_pred / flow_rate if flow_rate > 0 else 0
    pressure_per_rpm = pressure_pred / rpm if rpm > 0 else 0
    leak_risk_score = flow_rate - pressure_pred
    thermal_stress = temp * 2.9879 + vib * 100.0270 + pressure_pred * 0.0070 + flow_rate * 7.4e-5 + rpm * 4.7e-5 - 299.359
    
    l_inputs = [
        pressure_pred, flow_rate, temp, vib, rpm, hours, lat, lon,
        pressure_flow_ratio, pressure_per_rpm,
        leak_risk_score, flow_vib,
        thermal_stress, rpm_vib, wear_factor,
        zone_enc, block_enc, dist_center
    ]
    
    try:
        leak_prob = float(leakage_model.predict_proba([l_inputs])[0][1])
        leak_flag = 1 if leak_prob >= 0.50 else 0
    except Exception as err:
        print(f"Leakage Model error: {err}")
        leak_prob = 0.05
        leak_flag = 0
        
    return pressure_pred, leak_prob, leak_flag


# SMTP Mail Alert Sender
def send_email_alert(subject, body, cfg):
    if not cfg.get('alert_email'):
        return False, "Alert email not configured. Alert generated locally."
    
    try:
        msg = MIMEMultipart()
        msg['From'] = INTERNAL_SENDER_EMAIL
        msg['To'] = cfg['alert_email']
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'html'))
        
        server = smtplib.SMTP(INTERNAL_SMTP_HOST, INTERNAL_SMTP_PORT)
        server.starttls()
        server.login(INTERNAL_SMTP_USER, INTERNAL_SMTP_PASS)
        server.sendmail(msg['From'], msg['To'], msg.as_string())
        server.quit()
        return True, "Email Alert Sent successfully!"
    except Exception as e:
        return False, f"Failed sending email: {str(e)}"

# Background Real-time Pipeline Simulator
def run_pipeline_simulation():
    global df_pipes, live_alerts
    print("[SIMULATOR] Simulation thread started.")
    
    while True:
        # Sleep for 15 seconds between ticks
        time.sleep(15)
        
        if df_pipes is None or leakage_model is None or pressure_model is None:
            continue
            
        cfg = get_config()
        # Choose 2 random pipes to simulate changes
        sample_indices = random.sample(range(len(df_pipes)), min(2, len(df_pipes)))
        
        for idx in sample_indices:
            row = df_pipes.iloc[idx].copy()
            pipe_id = row['Pipe_ID']
            zone_office = row['Zone_Office']
            
            # Simulate a sensor anomaly: either a pressure drop or vibration spike
            anomaly_type = random.choice(['leak_leakage', 'vibration_spike', 'normal_fluctuation'])
            
            flow_rate = float(row['Flow_Rate'])
            pressure = float(row['Pressure'])
            vibration = float(row['Vibration'])
            temperature = float(row['Temperature'])
            rpm = float(row['RPM'])
            hours = float(row['Operational_Hours'])
            
            if anomaly_type == 'leak_leakage':
                # Flow rate increases, pressure drops significantly
                flow_rate *= random.uniform(1.15, 1.30)
                pressure *= random.uniform(0.60, 0.75)
                vibration *= random.uniform(1.10, 1.20)
            elif anomaly_type == 'vibration_spike':
                # Vibration spikes, pressure climbs
                vibration *= random.uniform(1.40, 1.80)
                pressure *= random.uniform(1.05, 1.15)
            else:
                # Normal operational noise
                flow_rate *= random.uniform(0.98, 1.02)
                pressure *= random.uniform(0.98, 1.02)
                vibration *= random.uniform(0.95, 1.05)
                
            # Run prediction on simulated attributes
            features = {
                'Flow_Rate': flow_rate,
                'Temperature': temperature,
                'Vibration': vibration,
                'RPM': rpm,
                'Operational_Hours': hours,
                'Latitude': row['Latitude'],
                'Longitude': row['Longitude'],
                'Zone_Enc': row['Zone_Enc'],
                'Block_Enc': row['Block_Enc']
            }
            
            pred_pressure, pred_leak_prob, pred_leak_flag = run_iterative_prediction(features)
            
            # Check thresholds
            trigger_alert = False
            reasons = []
            
            if pred_leak_prob >= cfg['leak_prob_threshold']:
                trigger_alert = True
                reasons.append(f"Leakage Probability ({pred_leak_prob:.1%}) exceeded threshold ({cfg['leak_prob_threshold']:.1%})")
                
            if pred_pressure <= cfg['pressure_threshold_low']:
                trigger_alert = True
                reasons.append(f"Water Pressure ({pred_pressure:.2f} PSI) dropped below low threshold ({cfg['pressure_threshold_low']:.2f} PSI)")
                
            if pred_pressure >= cfg['pressure_threshold_high']:
                trigger_alert = True
                reasons.append(f"Water Pressure ({pred_pressure:.2f} PSI) crossed high threshold ({cfg['pressure_threshold_high']:.2f} PSI)")
                
            if trigger_alert:
                alert_id = f"ALT-{int(time.time())}-{random.randint(1000, 9999)}"
                alert_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
                
                # Format body email
                reasons_html = "".join([f"<li>{r}</li>" for r in reasons])
                email_body = f"""
                <div style="font-family: Arial, sans-serif; border: 1px solid #ff4444; padding: 20px; border-radius: 8px; max-width: 600px;">
                    <h2 style="color: #d9534f; margin-top: 0;">⚠️ Smart Pipeline Failure Alert!</h2>
                    <p>Anomalies detected on pipeline segment <strong>{pipe_id}</strong> in <strong>{row['Zone_Name']}</strong>.</p>
                    <hr style="border: 0; border-top: 1px solid #eee;" />
                    <h3>Trigger Reasons:</h3>
                    <ul>{reasons_html}</ul>
                    <h3>Current Telemetry:</h3>
                    <table style="width: 100%; border-collapse: collapse;">
                        <tr><td style="padding: 5px 0;"><strong>Zone Office:</strong></td><td>{row['Zone_Office']}</td></tr>
                        <tr><td style="padding: 5px 0;"><strong>Ward:</strong></td><td>{row['Ward_Name']} (Ward No. {row['Ward_No']})</td></tr>
                        <tr><td style="padding: 5px 0;"><strong>Simulated Pressure:</strong></td><td>{pred_pressure:.2f} PSI</td></tr>
                        <tr><td style="padding: 5px 0;"><strong>Simulated Flow Rate:</strong></td><td>{flow_rate:.2f} L/s</td></tr>
                        <tr><td style="padding: 5px 0;"><strong>Vibration Level:</strong></td><td>{vibration:.3f} mm/s</td></tr>
                        <tr><td style="padding: 5px 0;"><strong>Coordinates:</strong></td><td>{row['Latitude']:.6f}, {row['Longitude']:.6f}</td></tr>
                    </table>
                    <p style="margin-top: 20px; font-size: 12px; color: #777;">This is an automated alert generated by Indore Smart Pipeline Prediction System.</p>
                </div>
                """
                
                # Attempt to send email
                mail_sent, msg_log = send_email_alert(
                    subject=f"⚠️ CRITICAL PIPELINE ALERT: {pipe_id} ({row['Zone_Name']})",
                    body=email_body,
                    cfg=cfg
                )
                
                alert_entry = {
                    "alert_id": alert_id,
                    "pipe_id": pipe_id,
                    "zone_office": zone_office,
                    "zone_name": row['Zone_Name'],
                    "ward_name": row['Ward_Name'],
                    "pressure": pred_pressure,
                    "flow_rate": flow_rate,
                    "vibration": vibration,
                    "leak_prob": pred_leak_prob,
                    "timestamp": alert_time,
                    "reasons": reasons,
                    "email_sent": mail_sent,
                    "log": msg_log
                }
                
                # Push to in-memory alerts
                live_alerts.insert(0, alert_entry)
                # Cap list size to 50
                live_alerts = live_alerts[:50]
                print(f"[ALERT TRIGGERED] Pipe: {pipe_id}, Risk: {pred_leak_prob:.1%}, Mail Status: {mail_sent}")

# Start Simulation Thread
sim_thread = threading.Thread(target=run_pipeline_simulation, daemon=True)
sim_thread.start()

# API Endpoints
@app.route('/')
def index():
    return app.send_static_file('index.html')

@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json() or {}
    username = data.get('username', '')
    password = data.get('password', '')
    
    cfg = get_config()
    admin_user = cfg.get('admin_username', 'admin')
    admin_pass = cfg.get('admin_password', 'admin123')
    
    if username == admin_user and password == admin_pass:
        token = secrets.token_hex(16)
        active_tokens.add(token)
        return jsonify({"token": token, "username": username})
    else:
        return jsonify({"error": "Invalid username or password"}), 401

@app.route('/api/logout', methods=['POST'])
def logout():
    auth_header = request.headers.get('Authorization', '')
    if auth_header.startswith('Bearer '):
        token = auth_header.split(' ')[1]
        active_tokens.discard(token)
    return jsonify({"message": "Logged out successfully"})

@app.route('/api/stats', methods=['GET'])
def get_stats():
    if df_pipes is None:
        return jsonify({"error": "Dataset not loaded"}), 500
        
    zone_office = request.args.get('zone_office', '')
    
    # Filter dataset based on Zone Office/Authority
    df_filtered = df_pipes
    if zone_office:
        df_filtered = df_pipes[df_pipes['Zone_Office'] == zone_office]
        
    if df_filtered.empty:
        return jsonify({
            "total_pipes": 0, "active_leaks": 0, "high_risk_pipes": 0,
            "avg_pressure": 0, "avg_flow_rate": 0,
            "ward_distribution": {}, "trend_data": []
        })
        
    total_pipes = len(df_filtered)
    # Define Risk categories using Leakage_Risk_Score and Leakage_Flag
    # Green: Leakage_Flag = 0 and Leakage_Risk_Score <= 15
    # Moderate Risk / Orange: Leakage_Flag = 0 and Leakage_Risk_Score > 15
    # Leakage / Red: Leakage_Flag = 1
    active_leaks = int(df_filtered['Leakage_Flag'].sum())
    high_risk_pipes = int(((df_filtered['Leakage_Flag'] == 0) & (df_filtered['Leakage_Risk_Score'] > 20)).sum())
    
    avg_pressure = float(df_filtered['Pressure'].mean())
    avg_flow_rate = float(df_filtered['Flow_Rate'].mean())
    
    # Calculate leak count by ward
    ward_counts = df_filtered[df_filtered['Leakage_Flag'] == 1]['Ward_Name'].value_counts().to_dict()
    ward_distribution = {str(k): int(v) for k, v in ward_counts.items()}
    
    # Trend analysis sampling (sample max 20 pipes for UI trend charts)
    sampled_trend = df_filtered.sample(min(20, len(df_filtered))).sort_values(by='Pipe_ID')
    trend_data = []
    for _, r in sampled_trend.iterrows():
        trend_data.append({
            "pipe_id": r["Pipe_ID"],
            "pressure": float(r["Pressure"]),
            "flow_rate": float(r["Flow_Rate"]),
            "risk_score": float(r["Leakage_Risk_Score"])
        })
        
    # Get unique Zone Offices for global filter dropdown
    authorities = sorted(df_pipes['Zone_Office'].dropna().unique().tolist())
    
    return jsonify({
        "total_pipes": total_pipes,
        "active_leaks": active_leaks,
        "high_risk_pipes": high_risk_pipes,
        "avg_pressure": round(avg_pressure, 2),
        "avg_flow_rate": round(avg_flow_rate, 2),
        "ward_distribution": ward_distribution,
        "trend_data": trend_data,
        "authorities": authorities
    })

@app.route('/api/pipes', methods=['GET'])
def get_pipes():
    if df_pipes is None:
        return jsonify({"error": "Dataset not loaded"}), 500
        
    zone_office = request.args.get('zone_office', '')
    
    df_filtered = df_pipes
    if zone_office:
        df_filtered = df_pipes[df_pipes['Zone_Office'] == zone_office]
        
    pipes_list = []
    for _, r in df_filtered.iterrows():
        # Determine status
        if r['Leakage_Flag'] == 1:
            status = 'leakage'
        elif r['Leakage_Risk_Score'] > 20:
            status = 'high_risk'
        else:
            status = 'normal'
            
        pipes_list.append({
            "pipe_id": r['Pipe_ID'],
            "latitude": float(r['Latitude']),
            "longitude": float(r['Longitude']),
            "pressure": round(float(r['Pressure']), 2),
            "flow_rate": round(float(r['Flow_Rate']), 2),
            "temperature": round(float(r['Temperature']), 2),
            "vibration": round(float(r['Vibration']), 3),
            "rpm": round(float(r['RPM']), 1),
            "hours": int(r['Operational_Hours']),
            "leak_flag": int(r['Leakage_Flag']),
            "risk_score": round(float(r['Leakage_Risk_Score']), 2),
            "status": status,
            "zone_name": r['Zone_Name'],
            "ward_name": r['Ward_Name'],
            "road": r['Zone_Road']
        })
        
    return jsonify(pipes_list)

@app.route('/api/predict', methods=['POST'])
def predict():
    if leakage_model is None or pressure_model is None:
        return jsonify({"error": "Models not loaded on server"}), 500
        
    data = request.get_json()
    if not data:
        return jsonify({"error": "No parameters provided"}), 400
        
    try:
        pred_pressure, pred_leak_prob, pred_leak_flag = run_iterative_prediction(data)
        
        # Determine recommendations based on status
        recommendations = []
        if pred_leak_flag == 1:
            severity = 'High'
            recommendations.append("IMMEDIATE ACTION REQUIRED: Deploy field repair team for ultrasonic testing at coordinates.")
            recommendations.append("Isolate pipeline segment by shutting off pressure controls to prevent further rupture.")
        elif pred_leak_prob > 0.40:
            severity = 'Medium'
            recommendations.append("Inspect joints and couplers at segment segment within 48 hours.")
            recommendations.append("Install acoustic leak logger to monitor transient pressure drops.")
        else:
            severity = 'Low'
            recommendations.append("Perform routine pipeline corridor inspection based on operational hours schedule.")
            
        return jsonify({
            "predicted_pressure": round(pred_pressure, 2),
            "leakage_probability": round(pred_leak_prob, 4),
            "leakage_flag": int(pred_leak_flag),
            "risk_score": round(float(data.get('Flow_Rate', 75.0)) - pred_pressure, 2),
            "severity": severity,
            "recommendations": recommendations
        })
    except Exception as e:
        return jsonify({"error": f"Prediction error: {str(e)}"}), 500

@app.route('/api/recommendations', methods=['GET'])
def get_recommendations():
    if df_pipes is None:
        return jsonify({"error": "Dataset not loaded"}), 500
        
    zone_office = request.args.get('zone_office', '')
    
    df_filtered = df_pipes
    if zone_office:
        df_filtered = df_pipes[df_pipes['Zone_Office'] == zone_office]
        
    # Generate predictive maintenance actions
    # High Priority: Leaking pipes
    # Medium Priority: Risk score > 20
    # Low Priority: Wear factor > 0.80
    high_rec = []
    med_rec = []
    low_rec = []
    
    # Sort pipes by risk score descending
    df_sorted = df_filtered.sort_values(by='Leakage_Risk_Score', ascending=False)
    
    for _, r in df_sorted.iterrows():
        pipe_id = r['Pipe_ID']
        zone = r['Zone_Name']
        road = r['Zone_Road']
        risk = r['Leakage_Risk_Score']
        wear = r['Wear_Factor']
        
        if r['Leakage_Flag'] == 1 and len(high_rec) < 5:
            high_rec.append({
                "pipe_id": pipe_id,
                "zone": zone,
                "road": road,
                "urgency": "CRITICAL",
                "risk_score": round(risk, 2),
                "wear": round(wear, 3),
                "action": "Leakage Flagged. Immediate deployment required to patch segment. Adjust pressure relief values."
            })
        elif risk > 20 and len(med_rec) < 5:
            med_rec.append({
                "pipe_id": pipe_id,
                "zone": zone,
                "road": road,
                "urgency": "HIGH RISK",
                "risk_score": round(risk, 2),
                "wear": round(wear, 3),
                "action": f"Flow-Pressure mismatch ({round(risk, 2)}). Conduct acoustic leak mapping and check joints for micro-cracks."
            })
        elif wear > 0.80 and len(low_rec) < 5:
            low_rec.append({
                "pipe_id": pipe_id,
                "zone": zone,
                "road": road,
                "urgency": "SCHEDULED MAINTENANCE",
                "risk_score": round(risk, 2),
                "wear": round(wear, 3),
                "action": f"Operational hours wear factor ({round(wear, 2)}) exceeded threshold. Schedule replacement within 30 days."
            })
            
    return jsonify({
        "critical": high_rec,
        "high": med_rec,
        "scheduled": low_rec
    })

@app.route('/api/alerts/config', methods=['GET', 'POST'])
def handle_alert_config():
    if not check_admin_auth():
        return jsonify({"error": "Unauthorized"}), 401
        
    if request.method == 'POST':
        data = request.get_json()
        if not data:
            return jsonify({"error": "No config data provided"}), 400
            
        cfg = get_config()
        # Update only allowed fields
        cfg['alert_email'] = data.get('alert_email', cfg.get('alert_email', ''))
        cfg['pressure_threshold_low'] = float(data.get('pressure_threshold_low', cfg['pressure_threshold_low']))
        cfg['pressure_threshold_high'] = float(data.get('pressure_threshold_high', cfg['pressure_threshold_high']))
        cfg['leak_prob_threshold'] = float(data.get('leak_prob_threshold', cfg['leak_prob_threshold']))
        
        if save_config(cfg):
            return_cfg = {
                "alert_email": cfg.get('alert_email', ''),
                "pressure_threshold_low": cfg['pressure_threshold_low'],
                "pressure_threshold_high": cfg['pressure_threshold_high'],
                "leak_prob_threshold": cfg['leak_prob_threshold']
            }
            return jsonify({"message": "Alert configurations saved successfully!", "config": return_cfg})
        else:
            return jsonify({"error": "Failed saving config"}), 500
            
    else:
        # GET method - return only non-sensitive config
        cfg = get_config()
        return_cfg = {
            "alert_email": cfg.get('alert_email', ''),
            "pressure_threshold_low": cfg.get('pressure_threshold_low', 45.0),
            "pressure_threshold_high": cfg.get('pressure_threshold_high', 75.0),
            "leak_prob_threshold": cfg.get('leak_prob_threshold', 0.70)
        }
        return jsonify(return_cfg)

@app.route('/api/alerts/send-test', methods=['POST'])
def send_test_email():
    if not check_admin_auth():
        return jsonify({"error": "Unauthorized"}), 401
        
    data = request.get_json() or {}
    cfg = get_config()
    
    # Use alert_email from request or config
    test_alert_email = data.get('alert_email', cfg.get('alert_email', ''))
    if not test_alert_email:
        return jsonify({"error": "No alert email configured. Please set an alert email first."}), 400
    
    test_cfg = {"alert_email": test_alert_email}
        
    test_body = """
    <div style="font-family: sans-serif; border: 1px solid #17a2b8; padding: 20px; border-radius: 8px;">
        <h2 style="color: #17a2b8; margin-top:0;">📡 Smart Pipeline Alerts - Test Email</h2>
        <p>This is a test notification confirming that your alert email is configured correctly.</p>
        <p><strong>System Status:</strong> Operational</p>
        <p><strong>Trigger Time:</strong> {}</p>
    </div>
    """.format(time.strftime('%Y-%m-%d %H:%M:%S'))
    
    success, log = send_email_alert(
        subject="🔔 Smart Pipeline Failure System - Test Alert",
        body=test_body,
        cfg=test_cfg
    )

    
    if success:
        return jsonify({"message": "Test Alert Sent Successfully!", "log": log})
    else:
        return jsonify({"error": log}), 500

@app.route('/api/alerts/live', methods=['GET'])
def get_live_alerts():
    return jsonify(live_alerts)

@app.route('/api/report', methods=['GET'])
def generate_report():
    if df_pipes is None:
        return jsonify({"error": "Dataset not loaded"}), 500
        
    zone_office = request.args.get('zone_office', '')
    
    df_filtered = df_pipes
    if zone_office:
        df_filtered = df_pipes[df_pipes['Zone_Office'] == zone_office]
        
    # Create output report filename
    report_name = f"Indore_Pipeline_Report_{int(time.time())}.csv"
    report_path = os.path.join(BASE_DIR, report_name)
    
    try:
        # Filter details to clean report format
        df_report = df_filtered[[
            'Pipe_ID', 'Zone_Name', 'Zone_Office', 'Zone_Road', 'Ward_Name', 'Ward_No',
            'Pressure', 'Flow_Rate', 'Temperature', 'Vibration', 'RPM', 'Operational_Hours',
            'Leakage_Flag', 'Leakage_Risk_Score', 'Wear_Factor'
        ]].copy()
        
        # Rename columns to human readable titles
        df_report.columns = [
            'Pipe ID', 'Zone Name', 'Zone Office', 'Zone Main Road', 'Ward Name', 'Ward Number',
            'Pressure (PSI)', 'Flow Rate (L/s)', 'Temperature (°C)', 'Vibration (mm/s)', 'RPM', 'Operational Hours',
            'Leakage Detected (0/1)', 'Leakage Risk Score', 'Equipment Wear Factor'
        ]
        
        df_report.to_csv(report_path, index=False)
        
        # Return file response and delete file after sending (using a generator or scheduling cleanup)
        return send_file(report_path, mimetype='text/csv', as_attachment=True, download_name=report_name)
    except Exception as e:
        return jsonify({"error": f"Failed to generate report: {str(e)}"}), 500

@app.route('/api/report/pdf', methods=['GET'])
def generate_pdf_report():
    if df_pipes is None:
        return jsonify({"error": "Dataset not loaded"}), 500
        
    scope = request.args.get('scope', 'bulk')
    pipe_id = request.args.get('pipe_id', '')
    days = request.args.get('days', 'current')
    zone_office = request.args.get('zone_office', '')
    
    # Force single pipe scope if pipe_id is provided
    if pipe_id:
        scope = 'single'
        
    report_name = f"Indore_Pipeline_Summary_{int(time.time())}.pdf"
    report_path = os.path.join(BASE_DIR, report_name)
    
    # Track temporary file paths for clean-up
    temp_files = []
    
    try:
        from reportlab.platypus import Image
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        import numpy as np
        
        doc = SimpleDocTemplate(
            report_path,
            pagesize=letter,
            rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36
        )
        
        styles = getSampleStyleSheet()
        
        # Custom Styles for Official Look
        title_style = ParagraphStyle(
            name='GovTitle',
            parent=styles['Heading1'],
            fontName='Helvetica-Bold',
            fontSize=16,
            leading=20,
            textColor=colors.HexColor('#0F2E59'),
            alignment=1, # Center
            spaceAfter=4
        )
        
        subtitle_style = ParagraphStyle(
            name='GovSubTitle',
            parent=styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=10,
            leading=13,
            textColor=colors.HexColor('#64748B'),
            alignment=1,
            spaceAfter=15
        )
        
        h2_style = ParagraphStyle(
            name='GovH2',
            parent=styles['Heading2'],
            fontName='Helvetica-Bold',
            fontSize=11,
            leading=14,
            textColor=colors.HexColor('#1E293B'),
            spaceBefore=12,
            spaceAfter=6,
            keepWithNext=True
        )
        
        body_style = ParagraphStyle(
            name='GovBody',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=8.5,
            leading=11,
            textColor=colors.HexColor('#334155')
        )
        
        body_bold = ParagraphStyle(
            name='GovBodyBold',
            parent=body_style,
            fontName='Helvetica-Bold'
        )
        
        hdr_style = ParagraphStyle(
            name='GovHdrText',
            parent=body_bold,
            textColor=colors.white
        )
        
        story = []
        
        # Official Heading
        story.append(Paragraph("INDORE MUNICIPAL CORPORATION", title_style))
        story.append(Paragraph("जल संसाधन एवं जल प्रदाय विभाग (WATER RESOURCES DEPARTMENT)", subtitle_style))
        
        if scope == 'single':
            # ============================================================
            # SINGLE PIPE ASSESSMENT REPORT
            # ============================================================
            pipe_row = df_pipes[df_pipes['Pipe_ID'] == pipe_id]
            if pipe_row.empty:
                return jsonify({"error": f"Pipeline segment {pipe_id} not found"}), 404
            
            pipe_row = pipe_row.iloc[0]
            
            zone_name = pipe_row.get('Zone_Name', 'Unknown')
            zone_off = pipe_row.get('Zone_Office', 'Unknown')
            zone_road = pipe_row.get('Zone_Road', 'Unknown')
            ward_name = pipe_row.get('Ward_Name', 'Unknown')
            ward_no = pipe_row.get('Ward_No', '-')
            lat = float(pipe_row.get('Latitude', 22.7))
            lon = float(pipe_row.get('Longitude', 75.8))
            pressure = float(pipe_row.get('Pressure', 0.0))
            flow = float(pipe_row.get('Flow_Rate', 0.0))
            temp = float(pipe_row.get('Temperature', 0.0))
            vib = float(pipe_row.get('Vibration', 0.0))
            rpm = float(pipe_row.get('RPM', 0.0))
            hours = int(pipe_row.get('Operational_Hours', 0))
            wear = float(pipe_row.get('Wear_Factor', 0.0))
            
            # Predict dynamic risk features for this specific pipe
            features = {
                'Flow_Rate': flow,
                'Temperature': temp,
                'Vibration': vib,
                'RPM': rpm,
                'Operational_Hours': hours,
                'Latitude': lat,
                'Longitude': lon,
                'Zone_Enc': int(pipe_row.get('Zone_Enc', 3)),
                'Block_Enc': int(pipe_row.get('Block_Enc', 1))
            }
            pred_pressure, pred_leak_prob, pred_leak_flag = run_iterative_prediction(features)
            risk_score = flow - pred_pressure
            
            severity = 'Low'
            if pred_leak_flag == 1 or pred_leak_prob >= 0.70:
                severity = 'High'
            elif pred_leak_prob >= 0.40:
                severity = 'Medium'
            
            # Metadata Block
            meta_data = [
                [Paragraph(f"<b>Assessment Pipe ID:</b> {pipe_id}", body_style), 
                 Paragraph(f"<b>Report Load Date/Time:</b> {time.strftime('%Y-%m-%d %H:%M:%S')}", body_style)],
                [Paragraph(f"<b>Authority Zone Office:</b> {zone_off}", body_style), 
                 Paragraph(f"<b>Location Main Road:</b> {zone_road}", body_style)],
                [Paragraph(f"<b>Ward Name & Number:</b> {ward_name} (Ward No. {ward_no})", body_style), 
                 Paragraph(f"<b>GIS Coordinates:</b> {lat:.6f}, {lon:.6f}", body_style)]
            ]
            t_meta = Table(meta_data, colWidths=[270, 270])
            t_meta.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#F8FAFC')),
                ('PADDING', (0,0), (-1,-1), 6),
                ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#E2E8F0')),
            ]))
            story.append(t_meta)
            story.append(Spacer(1, 10))
            
            # 1. Telemetry Snapshot
            story.append(Paragraph("1. Current Telemetry Snapshot", h2_style))
            p_status = "Normal (Healthy)"
            if pressure < 45.0: p_status = "ANOMALY: LOW PRESSURE"
            elif pressure > 75.0: p_status = "ANOMALY: HIGH PRESSURE"
            
            v_status = "Normal (Low Wear)"
            if vib > 4.0: v_status = "CRITICAL VIBRATION"
            elif vib > 2.8: v_status = "MODERATE VIBRATION"
            
            snap_headers = [
                Paragraph("<b>Telemetry Parameter</b>", hdr_style), 
                Paragraph("<b>Current Sensor Value</b>", hdr_style), 
                Paragraph("<b>Hydraulic Status</b>", hdr_style)
            ]
            snap_rows = [
                snap_headers,
                [Paragraph("Water Pressure", body_style), Paragraph(f"{pressure:.2f} PSI", body_style), Paragraph(p_status, body_bold if "ANOMALY" in p_status else body_style)],
                [Paragraph("Water Flow Rate", body_style), Paragraph(f"{flow:.2f} L/s", body_style), Paragraph("Active Supply Segment", body_style)],
                [Paragraph("Vibration Level", body_style), Paragraph(f"{vib:.3f} mm/s", body_style), Paragraph(v_status, body_bold if "CRITICAL" in v_status else body_style)],
                [Paragraph("Water Temperature", body_style), Paragraph(f"{temp:.1f} °C", body_style), Paragraph("Normal Operational Range", body_style)],
                [Paragraph("Pump RPM Speed", body_style), Paragraph(f"{rpm:.1f} RPM", body_style), Paragraph("Operational", body_style)],
                [Paragraph("Equipment Wear Factor", body_style), Paragraph(f"{wear:.3f}", body_style), Paragraph("Critical replacement needed" if wear > 0.8 else "Normal", body_bold if wear > 0.8 else body_style)]
            ]
            t_snap = Table(snap_rows, colWidths=[200, 150, 190])
            t_snap.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#0F2E59')),
                ('PADDING', (0,0), (-1,-1), 5),
                ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#CBD5E1')),
                ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#F8FAFC')])
            ]))
            story.append(t_snap)
            story.append(Spacer(1, 10))
            
            # 2. Historical Trend Chart
            if days in ['1', '2']:
                days_int = int(days)
                hours_to_sim = days_int * 24
                
                # Seeding random walk based on pipe ID
                try:
                    seed_val = int(pipe_id.split('-')[-1])
                except Exception:
                    seed_val = 42
                np.random.seed(seed_val)
                
                pressures_sim = []
                flows_sim = []
                vibs_sim = []
                
                p_val = pressure
                f_val = flow
                v_val = vib
                
                for _ in range(hours_to_sim):
                    pressures_sim.insert(0, p_val)
                    flows_sim.insert(0, f_val)
                    vibs_sim.insert(0, v_val)
                    
                    p_val += float(np.random.normal(0, 1.0))
                    f_val += float(np.random.normal(0, 1.3))
                    v_val += float(np.random.normal(0, 0.04))
                    
                    p_val = max(20.0, min(95.0, p_val))
                    f_val = max(10.0, min(150.0, f_val))
                    v_val = max(0.5, min(5.0, v_val))
                    
                # Create Matplotlib Plot
                fig, ax1 = plt.subplots(figsize=(6.0, 2.0))
                ax2 = ax1.twinx()
                time_axis = list(range(-hours_to_sim + 1, 1))
                
                ax1.plot(time_axis, pressures_sim, color='#0ea5e9', label='Pressure (PSI)', linewidth=1.5)
                ax2.plot(time_axis, flows_sim, color='#8b5cf6', label='Flow Rate (L/s)', linewidth=1.5)
                
                ax1.set_xlabel('Hours Ago')
                ax1.set_ylabel('Pressure (PSI)', color='#0ea5e9')
                ax2.set_ylabel('Flow Rate (L/s)', color='#8b5cf6')
                ax1.tick_params(axis='y', labelcolor='#0ea5e9')
                ax2.tick_params(axis='y', labelcolor='#8b5cf6')
                ax1.grid(True, linestyle=':', alpha=0.5)
                
                plt.title(f"Telemetry Trend Analysis - Last {hours_to_sim} Hours ({days_int} Day)", fontsize=9, fontweight='bold', pad=5)
                fig.tight_layout()
                
                chart_name = f"temp_chart_{pipe_id}_{int(time.time())}.png"
                chart_path = os.path.join(BASE_DIR, chart_name)
                plt.savefig(chart_path, dpi=150, bbox_inches='tight')
                plt.close()
                temp_files.append(chart_path)
                
                story.append(Paragraph(f"2. Historical Telemetry Trend Analysis (Last {days_int} Day / {hours_to_sim} Hours)", h2_style))
                story.append(Image(chart_path, width=420, height=140))
                story.append(Spacer(1, 10))
                
                # Stats calculation
                min_p = min(pressures_sim)
                max_p = max(pressures_sim)
                avg_p = sum(pressures_sim) / len(pressures_sim)
                min_f = min(flows_sim)
                max_f = max(flows_sim)
                avg_f = sum(flows_sim) / len(flows_sim)
                max_v = max(vibs_sim)
                
                stats_rows = [
                    [Paragraph("<b>Historical Metric Summary</b>", hdr_style), 
                     Paragraph("<b>Current Value</b>", hdr_style), 
                     Paragraph("<b>Minimum Value</b>", hdr_style), 
                     Paragraph("<b>Maximum Value</b>", hdr_style), 
                     Paragraph("<b>Average Value</b>", hdr_style)],
                    [Paragraph("Water Pressure (PSI)", body_style), Paragraph(f"{pressure:.2f}", body_style), Paragraph(f"{min_p:.2f}", body_style), Paragraph(f"{max_p:.2f}", body_style), Paragraph(f"{avg_p:.2f}", body_style)],
                    [Paragraph("Water Flow Rate (L/s)", body_style), Paragraph(f"{flow:.2f}", body_style), Paragraph(f"{min_f:.2f}", body_style), Paragraph(f"{max_f:.2f}", body_style), Paragraph(f"{avg_f:.2f}", body_style)],
                    [Paragraph("Vibration Level (mm/s)", body_style), Paragraph(f"{vib:.3f}", body_style), Paragraph("-", body_style), Paragraph(f"{max_v:.3f}", body_style), Paragraph("-", body_style)]
                ]
                t_stats = Table(stats_rows, colWidths=[180, 90, 90, 90, 90])
                t_stats.setStyle(TableStyle([
                    ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#0F2E59')),
                    ('PADDING', (0,0), (-1,-1), 4),
                    ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#CBD5E1')),
                    ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#F8FAFC')])
                ]))
                story.append(t_stats)
                story.append(Spacer(1, 10))
            
            # 3. AI Predictions
            story.append(Paragraph("3. AI Predictive Diagnostics & Recommendations", h2_style))
            
            sev_color = 'green'
            if severity == 'High': sev_color = 'red'
            elif severity == 'Medium': sev_color = 'orange'
            
            diag_rows = [
                [Paragraph("<b>Model Parameter</b>", hdr_style), Paragraph("<b>Diagnostic Outcome</b>", hdr_style), Paragraph("<b>Alert Status & Action</b>", hdr_style)],
                [Paragraph("Leakage Probability", body_style), Paragraph(f"<b>{pred_leak_prob:.1%}</b>", body_style), Paragraph(f"<font color='{sev_color}'><b>{severity} Risk</b></font>", body_style)],
                [Paragraph("Predicted Grid Pressure", body_style), Paragraph(f"{pred_pressure:.2f} PSI", body_style), Paragraph("Expected pressure drop" if pred_leak_prob > 0.40 else "Steady pressure", body_style)],
                [Paragraph("Flow-Pressure Anomaly Score", body_style), Paragraph(f"{risk_score:.2f}", body_style), Paragraph("Major mismatch" if risk_score > 20 else "Normal hydraulics", body_style)]
            ]
            t_diag = Table(diag_rows, colWidths=[180, 160, 200])
            t_diag.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#0F2E59')),
                ('PADDING', (0,0), (-1,-1), 5),
                ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#CBD5E1')),
                ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#F8FAFC')])
            ]))
            story.append(t_diag)
            story.append(Spacer(1, 10))
            
            # Recommendations list
            story.append(Paragraph("<b>Preventive Maintenance Action Items:</b>", body_bold))
            recs = []
            if severity == 'High':
                recs.append("IMMEDIATE ACTION REQUIRED: Deploy field repair team for ultrasonic testing at coordinates.")
                recs.append("Isolate pipeline segment by shutting off pressure controls to prevent further rupture.")
                recs.append("Inspect joints and couplers at coordinates for physical damage or rupture.")
            elif severity == 'Medium':
                recs.append("Inspect joints and couplers at segment segment within 48 hours.")
                recs.append("Install acoustic leak logger to monitor transient pressure drops.")
            else:
                recs.append("Perform routine pipeline corridor inspection based on operational hours schedule.")
                
            if wear > 0.80:
                recs.append("Critical Wear Factor: Schedule pipe segment replacement/re-lining within 30 days.")
            elif wear > 0.50:
                recs.append("Moderate mechanical wear. Monitor vibration parameters in next scheduled cycle.")
                
            bullets = "".join([f"&bull; {r}<br/>" for r in recs])
            story.append(Paragraph(bullets, body_style))
            
        else:
            # ============================================================
            # BULK / ZONE SUMMARY REPORT
            # ============================================================
            df_filtered = df_pipes
            if zone_office:
                df_filtered = df_pipes[df_pipes['Zone_Office'] == zone_office]
                
            total_pipes = len(df_filtered)
            active_leaks = int(df_filtered['Leakage_Flag'].sum())
            high_risk_pipes = int(((df_filtered['Leakage_Flag'] == 0) & (df_filtered['Leakage_Risk_Score'] > 20)).sum())
            avg_pressure = float(df_filtered['Pressure'].mean()) if total_pipes > 0 else 0
            avg_flow = float(df_filtered['Flow_Rate'].mean()) if total_pipes > 0 else 0
            
            # Metadata Table
            meta_data = [
                [Paragraph("<b>Report Type:</b> Pipeline Assessment Summary", body_style), 
                 Paragraph(f"<b>Report Load Date/Time:</b> {time.strftime('%Y-%m-%d %H:%M:%S')}", body_style)],
                [Paragraph(f"<b>Authority Zone:</b> {zone_office if zone_office else 'All Indore Zones'}", body_style), 
                 Paragraph("<b>Status:</b> Official / Confirmed Summary", body_style)]
            ]
            t_meta = Table(meta_data, colWidths=[270, 270])
            t_meta.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#F8FAFC')),
                ('PADDING', (0,0), (-1,-1), 6),
                ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#E2E8F0')),
            ]))
            story.append(t_meta)
            story.append(Spacer(1, 10))
            
            # 1. Grid Summary Stats
            story.append(Paragraph("1. Grid Analytics Summary", h2_style))
            stats_data = [
                [Paragraph("<b>Metric</b>", hdr_style), Paragraph("<b>Value</b>", hdr_style), Paragraph("<b>Reference Threshold Limit</b>", hdr_style)],
                [Paragraph("Total Monitored Segments", body_style), Paragraph(str(total_pipes), body_style), Paragraph("-", body_style)],
                [Paragraph("<font color='red'>Active Failure/Leakage Points</font>", body_style), Paragraph(str(active_leaks), body_bold), Paragraph("0 Tolerance Limit", body_style)],
                [Paragraph("<font color='orange'>High Risk Segments</font>", body_style), Paragraph(str(high_risk_pipes), body_style), Paragraph("Risk Score > 20.0", body_style)],
                [Paragraph("Average Pressure", body_style), Paragraph(f"{avg_pressure:.2f} PSI", body_style), Paragraph("45.0 - 75.0 PSI", body_style)],
                [Paragraph("Average Flow Rate", body_style), Paragraph(f"{avg_flow:.2f} L/s", body_style), Paragraph("-", body_style)]
            ]
            t_stats = Table(stats_data, colWidths=[220, 100, 220])
            t_stats.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#0F2E59')),
                ('PADDING', (0,0), (-1,-1), 5),
                ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#CBD5E1')),
                ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#F8FAFC')])
            ]))
            story.append(t_stats)
            story.append(Spacer(1, 10))
            
            # 2. Zone-wise summary table
            story.append(Paragraph("2. Zone-wise Grid Distribution & Prediction Metrics", h2_style))
            zone_groups = df_filtered.groupby('Zone_Name')
            zone_headers = [
                Paragraph("<b>Zone Name</b>", hdr_style),
                Paragraph("<b>Total Pipes</b>", hdr_style),
                Paragraph("<b>Leaks</b>", hdr_style),
                Paragraph("<b>High Risk</b>", hdr_style),
                Paragraph("<b>Avg Press</b>", hdr_style),
                Paragraph("<b>Avg Flow</b>", hdr_style)
            ]
            zone_rows = [zone_headers]
            for z_name, z_group in zone_groups:
                z_total = len(z_group)
                z_leaks = int(z_group['Leakage_Flag'].sum())
                z_hr = int(((z_group['Leakage_Flag'] == 0) & (z_group['Leakage_Risk_Score'] > 20)).sum())
                z_avg_p = float(z_group['Pressure'].mean())
                z_avg_f = float(z_group['Flow_Rate'].mean())
                zone_rows.append([
                    Paragraph(z_name, body_style),
                    Paragraph(str(z_total), body_style),
                    Paragraph(f"<font color='red'><b>{z_leaks}</b></font>" if z_leaks > 0 else "0", body_style),
                    Paragraph(f"<font color='orange'><b>{z_hr}</b></font>" if z_hr > 0 else "0", body_style),
                    Paragraph(f"{z_avg_p:.2f} PSI", body_style),
                    Paragraph(f"{z_avg_f:.2f} L/s", body_style)
                ])
            t_zones = Table(zone_rows, colWidths=[140, 80, 80, 80, 80, 80])
            t_zones.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#0F2E59')),
                ('PADDING', (0,0), (-1,-1), 4),
                ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#CBD5E1')),
                ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#F8FAFC')])
            ]))
            story.append(t_zones)
            story.append(Spacer(1, 10))
            
            # 3. Embed Dynamic Matplotlib plots (GIS Scatter Map and Ward failure Bar Chart)
            story.append(Paragraph("3. GIS Pipeline Risk Mapping & Ward Hotspots Summary", h2_style))
            
            # Chart 1: GIS risk scatter plot (represents zone wise mapping)
            fig_gis, ax = plt.subplots(figsize=(4.0, 3.0))
            normal = df_filtered[(df_filtered['Leakage_Flag'] == 0) & (df_filtered['Leakage_Risk_Score'] <= 20)]
            high_risk = df_filtered[(df_filtered['Leakage_Flag'] == 0) & (df_filtered['Leakage_Risk_Score'] > 20)]
            leaks_pts = df_filtered[df_filtered['Leakage_Flag'] == 1]
            
            ax.scatter(normal['Longitude'], normal['Latitude'], color='#10b981', label='Normal', s=4, alpha=0.5)
            ax.scatter(high_risk['Longitude'], high_risk['Latitude'], color='#f59e0b', label='High Risk', s=8, alpha=0.7)
            ax.scatter(leaks_pts['Longitude'], leaks_pts['Latitude'], color='#ef4444', label='Leak Node', s=14, alpha=0.9)
            
            ax.set_xlabel('Longitude', fontsize=7)
            ax.set_ylabel('Latitude', fontsize=7)
            ax.set_title('GIS Network Anomaly Mapping', fontsize=8, fontweight='bold')
            ax.legend(loc='upper right', fontsize=6)
            ax.grid(True, linestyle=':', alpha=0.4)
            fig_gis.tight_layout()
            
            gis_chart_name = f"temp_gis_{int(time.time())}.png"
            gis_chart_path = os.path.join(BASE_DIR, gis_chart_name)
            plt.savefig(gis_chart_path, dpi=150, bbox_inches='tight')
            plt.close()
            temp_files.append(gis_chart_path)
            
            # Chart 2: Ward leaks bar chart
            fig_ward, ax = plt.subplots(figsize=(4.0, 3.0))
            ward_counts = df_filtered[df_filtered['Leakage_Flag'] == 1]['Ward_Name'].value_counts().head(10)
            if not ward_counts.empty:
                ward_counts.plot(kind='barh', color='#ef4444', edgecolor='#b91c1c', ax=ax)
                ax.set_xlabel('Leaks Count', fontsize=7)
                ax.set_ylabel('Ward Name', fontsize=7)
                ax.set_title('Ward Failure Frequency Hotspots', fontsize=8, fontweight='bold')
                ax.invert_yaxis()
                ax.tick_params(axis='both', which='major', labelsize=6)
            else:
                ax.text(0.5, 0.5, 'No Active Leaks Recorded', horizontalalignment='center', verticalalignment='center')
                ax.set_title('Ward Failure Frequency Hotspots', fontsize=8, fontweight='bold')
            fig_ward.tight_layout()
            
            ward_chart_name = f"temp_ward_{int(time.time())}.png"
            ward_chart_path = os.path.join(BASE_DIR, ward_chart_name)
            plt.savefig(ward_chart_path, dpi=150, bbox_inches='tight')
            plt.close()
            temp_files.append(ward_chart_path)
            
            # Display charts side-by-side inside a table
            chart_row = [
                Image(gis_chart_path, width=255, height=191),
                Image(ward_chart_path, width=255, height=191)
            ]
            t_charts = Table([chart_row], colWidths=[270, 270])
            t_charts.setStyle(TableStyle([
                ('ALIGN', (0,0), (-1,-1), 'CENTER'),
                ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
                ('PADDING', (0,0), (-1,-1), 0),
            ]))
            story.append(t_charts)
            story.append(Spacer(1, 10))
            
            # 4. Critical Anomalies List
            story.append(Paragraph("4. Critical Anomalies List (Urgent Repairs)", h2_style))
            df_leaks = df_filtered[df_filtered['Leakage_Flag'] == 1].head(15)
            if len(df_leaks) == 0:
                story.append(Paragraph("No active failure/leakage points reported under this jurisdiction.", body_style))
            else:
                leak_headers = [Paragraph("<b>Pipe ID</b>", hdr_style), Paragraph("<b>Ward</b>", hdr_style), Paragraph("<b>Zone Road</b>", hdr_style), Paragraph("<b>Pressure (PSI)</b>", hdr_style), Paragraph("<b>Flow (L/s)</b>", hdr_style)]
                leak_rows = [leak_headers]
                for _, r in df_leaks.iterrows():
                    leak_rows.append([
                        Paragraph(str(r['Pipe_ID']), body_style),
                        Paragraph(str(r['Ward_Name']), body_style),
                        Paragraph(str(r['Zone_Road']), body_style),
                        Paragraph(f"{r['Pressure']:.2f}", body_style),
                        Paragraph(f"{r['Flow_Rate']:.2f}", body_style)
                    ])
                t_leaks = Table(leak_rows, colWidths=[90, 100, 200, 75, 75])
                t_leaks.setStyle(TableStyle([
                    ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#EF4444')),
                    ('PADDING', (0,0), (-1,-1), 5),
                    ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#CBD5E1')),
                    ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#FEF2F2')])
                ]))
                story.append(t_leaks)
                
        # Signature block
        story.append(Spacer(1, 15))
        sig_data = [
            [Paragraph("", body_style), Paragraph("<b>Authorized Signatory</b><br/>Water Works Department<br/>Indore Municipal Corporation", body_style)]
        ]
        t_sig = Table(sig_data, colWidths=[340, 200])
        t_sig.setStyle(TableStyle([
            ('ALIGN', (1,0), (1,0), 'RIGHT'),
            ('PADDING', (0,0), (-1,-1), 10),
            ('TOPPADDING', (0,0), (-1,-1), 20)
        ]))
        story.append(KeepTogether(t_sig))
        
        doc.build(story)
        return send_file(report_path, mimetype='application/pdf', as_attachment=True, download_name=report_name)
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": f"Failed to generate PDF: {str(e)}"}), 500
        
    finally:
        # Clean up temporary chart images
        for f in temp_files:
            try:
                if os.path.exists(f):
                    os.remove(f)
            except Exception as ex:
                print(f"Error deleting temporary image {f}: {ex}")

if __name__ == '__main__':
    # Run server
    app.run(host='0.0.0.0', port=5000, debug=True)
