import os
import unittest
import json
import app as flask_app  # Imports app.py

class TestPipelineFailureSystem(unittest.TestCase):
    
    def setUp(self):
        # Create Flask test client
        self.app = flask_app.app.test_client()
        self.app.testing = True

    def test_resources_loaded(self):
        """Verify that the Indore dataset and models loaded successfully"""
        print("\n--- Testing Resources Loading ---")
        self.assertIsNotNone(flask_app.df_pipes, "Dataset is not loaded.")
        self.assertIsNotNone(flask_app.leakage_model, "Leakage Random Forest model is not loaded.")
        self.assertIsNotNone(flask_app.pressure_model, "Pressure Random Forest model is not loaded.")
        print("[OK] Dataset and Model pickles loaded successfully.")

    def test_api_stats(self):
        """Test the statistics API endpoint"""
        print("\n--- Testing GET /api/stats ---")
        response = self.app.get('/api/stats')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        
        self.assertIn("total_pipes", data)
        self.assertIn("active_leaks", data)
        self.assertIn("high_risk_pipes", data)
        self.assertIn("avg_pressure", data)
        self.assertIn("avg_flow_rate", data)
        self.assertIn("ward_distribution", data)
        self.assertIn("trend_data", data)
        self.assertIn("authorities", data)
        
        print(f"[OK] Stats fetched: Total pipes = {data['total_pipes']}, Active leaks = {data['active_leaks']}")

    def test_api_pipes(self):
        """Test the list of pipes GIS endpoint"""
        print("\n--- Testing GET /api/pipes ---")
        response = self.app.get('/api/pipes')
        self.assertEqual(response.status_code, 200)
        pipes = json.loads(response.data)
        
        self.assertIsInstance(pipes, list)
        if len(pipes) > 0:
            first_pipe = pipes[0]
            self.assertIn("pipe_id", first_pipe)
            self.assertIn("latitude", first_pipe)
            self.assertIn("longitude", first_pipe)
            self.assertIn("pressure", first_pipe)
            self.assertIn("flow_rate", first_pipe)
            self.assertIn("status", first_pipe)
            print(f"[OK] Pipes list fetched. First Pipe: {first_pipe['pipe_id']} at ({first_pipe['latitude']}, {first_pipe['longitude']})")
        else:
            print("[WARNING] Pipes list returned empty.")

    def test_api_predict(self):
        """Test the iterative solver prediction model endpoint"""
        print("\n--- Testing POST /api/predict ---")
        payload = {
            "Flow_Rate": 85.0,
            "Temperature": 105.0,
            "Vibration": 3.4,
            "RPM": 2100.0,
            "Operational_Hours": 6000.0,
            "Latitude": 22.695,
            "Longitude": 75.844,
            "Zone_Enc": 3,
            "Block_Enc": 1
        }
        
        response = self.app.post('/api/predict', 
                                 data=json.dumps(payload),
                                 content_type='application/json')
        
        self.assertEqual(response.status_code, 200)
        outputs = json.loads(response.data)
        
        self.assertIn("predicted_pressure", outputs)
        self.assertIn("leakage_probability", outputs)
        self.assertIn("leakage_flag", outputs)
        self.assertIn("risk_score", outputs)
        self.assertIn("severity", outputs)
        self.assertIn("recommendations", outputs)
        
        print(f"[OK] Iterative Prediction result: Pressure = {outputs['predicted_pressure']} PSI, Leakage Probability = {outputs['leakage_probability'] * 100:.2f}%, Severity = {outputs['severity']}")

    def test_api_recommendations(self):
        """Test recommendations API"""
        print("\n--- Testing GET /api/recommendations ---")
        response = self.app.get('/api/recommendations')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn("critical", data)
        self.assertIn("high", data)
        self.assertIn("scheduled", data)
        print(f"[OK] Recommendations fetched: Critical items = {len(data['critical'])}")

    def test_api_config(self):
        """Test alert configurations endpoint"""
        print("\n--- Testing GET /api/alerts/config ---")
        flask_app.active_tokens.add("test-token-123")
        response = self.app.get('/api/alerts/config', headers={"Authorization": "Bearer test-token-123"})
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn("alert_email", data)
        self.assertIn("leak_prob_threshold", data)
        self.assertIn("pressure_threshold_low", data)
        self.assertIn("pressure_threshold_high", data)
        print("[OK] SMTP Configurations retrieved successfully using Bearer Auth.")

    def test_api_auth(self):
        """Test login and logout endpoints"""
        print("\n--- Testing POST /api/login and /api/logout ---")
        # Test success login
        payload = {"username": "admin", "password": "admin123"}
        response = self.app.post('/api/login',
                                 data=json.dumps(payload),
                                 content_type='application/json')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn("token", data)
        token = data["token"]
        print("[OK] Login successful with correct credentials.")

        # Test failed login
        fail_payload = {"username": "admin", "password": "wrong_password"}
        response = self.app.post('/api/login',
                                 data=json.dumps(fail_payload),
                                 content_type='application/json')
        self.assertEqual(response.status_code, 401)
        print("[OK] Login rejected with incorrect credentials.")

        # Test request using the login token
        response = self.app.get('/api/alerts/config', headers={"Authorization": f"Bearer {token}"})
        self.assertEqual(response.status_code, 200)
        print("[OK] Configuration accessed successfully using login token.")

        # Test logout
        logout_response = self.app.post('/api/logout', headers={"Authorization": f"Bearer {token}"})
        self.assertEqual(logout_response.status_code, 200)
        print("[OK] Logout endpoint returned 200.")

        # Verify token is invalid after logout
        post_logout_response = self.app.get('/api/alerts/config', headers={"Authorization": f"Bearer {token}"})
        self.assertEqual(post_logout_response.status_code, 401)
        print("[OK] Access rejected after logout.")

    def test_api_pdf_report(self):
        """Test PDF summary report endpoint (Bulk Grid default)"""
        print("\n--- Testing GET /api/report/pdf (Bulk Grid) ---")
        response = self.app.get('/api/report/pdf')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.mimetype, 'application/pdf')
        print("[OK] Bulk PDF Summary Report generated successfully with correct headers.")

    def test_api_pdf_report_single_current(self):
        """Test PDF single pipe assessment report (Current snapshot)"""
        print("\n--- Testing GET /api/report/pdf (Single Pipe Current) ---")
        response = self.app.get('/api/report/pdf?scope=single&pipe_id=IND-PIPE-0003&days=current')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.mimetype, 'application/pdf')
        print("[OK] Single Pipe Assessment (Current) generated successfully.")

    def test_api_pdf_report_single_history(self):
        """Test PDF single pipe assessment report (with 2-days simulated history trend)"""
        print("\n--- Testing GET /api/report/pdf (Single Pipe 48 Hours History) ---")
        response = self.app.get('/api/report/pdf?scope=single&pipe_id=IND-PIPE-0003&days=2')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.mimetype, 'application/pdf')
        print("[OK] Single Pipe Assessment (48h History) generated successfully.")

    def test_api_pdf_report_bulk_zone(self):
        """Test PDF bulk report filtered by specific zone office"""
        print("\n--- Testing GET /api/report/pdf (Bulk Zone Office) ---")
        response = self.app.get('/api/report/pdf?scope=bulk&zone_office=Sirpur%20Zone%20Office')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.mimetype, 'application/pdf')
        print("[OK] Bulk Zone Office PDF Report generated successfully.")

if __name__ == '__main__':
    unittest.main()
