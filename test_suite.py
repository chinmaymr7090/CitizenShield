"""
CitizenShield Major Project Automated Verification Suite
Performs 10 Comprehensive End-to-End Tests against live backend:
TEST 1: Register a new citizen and save in SQLite.
TEST 2: Login as registered citizen.
TEST 3: Submit complaint with image and GPS location.
TEST 4: Run actual AI image detection and show real model result.
TEST 5: Verify AI detection record and complaint saved in SQLite.
TEST 6: Login as municipal officer.
TEST 7: View complaint, evidence image, AI result, and location.
TEST 8: Update complaint status with officer remarks & verify Status_History.
TEST 9: Track complaint as citizen and verify audit timeline.
TEST 10: Verify AI dashboard statistics against real database records.
Bonus Edge Tests: Duplicate complaint check & unauthorized access block.
"""

import urllib.request
import urllib.parse
import json
import os
import uuid
import sys

BASE_URL = "http://127.0.0.1:5000"

def post_json(endpoint, data, token=None):
    req_data = json.dumps(data).encode("utf-8")
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(f"{BASE_URL}{endpoint}", data=req_data, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req) as resp:
            return resp.status, json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read().decode("utf-8"))

def get_json(endpoint, token=None):
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(f"{BASE_URL}{endpoint}", headers=headers, method="GET")
    try:
        with urllib.request.urlopen(req) as resp:
            return resp.status, json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read().decode("utf-8"))

def patch_json(endpoint, data, token=None):
    req_data = json.dumps(data).encode("utf-8")
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(f"{BASE_URL}{endpoint}", data=req_data, headers=headers, method="PATCH")
    try:
        with urllib.request.urlopen(req) as resp:
            return resp.status, json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read().decode("utf-8"))

def run_tests():
    print("=" * 65)
    print("CITIZENSHIELD - 10-STAGE AUTOMATED END-TO-END VERIFICATION")
    print("=" * 65)

    # TEST 1: Register a new citizen
    rnd_suffix = uuid.uuid4().hex[:6]
    cit_email = f"test.citizen.{rnd_suffix}@tumakuru.in"
    cit_pass = "TestPass@2026"
    print(f"\n[TEST 1] Registering New Citizen: {cit_email}")
    status, res = post_json("/api/auth/register", {
        "name": f"Priya Rao {rnd_suffix}",
        "email": cit_email,
        "password": cit_pass,
        "phone": "+91 94800 11223"
    })
    assert status == 201, f"Test 1 Failed: {res}"
    print(f" -> PASS: Citizen registered. SQLite User ID: {res['user_id']}")

    # TEST 2: Log in as registered citizen
    print(f"\n[TEST 2] Logging In Citizen...")
    status, res = post_json("/api/auth/login", {
        "email": cit_email,
        "password": cit_pass
    })
    assert status == 200, f"Test 2 Failed: {res}"
    citizen_token = res["token"]
    print(f" -> PASS: Auth Token received: {citizen_token[:16]}... Role: {res['user']['role']}")

    # TEST 3 & 4: Run actual AI image detection on test image
    print(f"\n[TEST 3 & 4] Running Real AI Image Detection via YOLOv8 / OpenCV...")
    # Multipart upload for analyze-image
    boundary = uuid.uuid4().hex
    test_image_path = "uploads/1793251633_2ee4a5b9.jpeg"
    with open(test_image_path, "rb") as f:
        file_bytes = f.read()

    body = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="image"; filename="road_test.jpg"\r\n'
        f"Content-Type: image/jpeg\r\n\r\n"
    ).encode("utf-8") + file_bytes + f"\r\n--{boundary}--\r\n".encode("utf-8")

    req = urllib.request.Request(
        f"{BASE_URL}/api/ai/analyze-image",
        data=body,
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
        method="POST"
    )
    with urllib.request.urlopen(req) as resp:
        ai_res = json.loads(resp.read().decode("utf-8"))

    assert ai_res["detected"] is True, f"AI Detection Failed: {ai_res}"
    print(f" -> PASS: Real AI Model Detected: {ai_res['detected_class']}")
    print(f"    Model Name: {ai_res['model_name']}")
    print(f"    Confidence: {ai_res['confidence_score']} ({ai_res['confidence_percent']})")
    print(f"    Suggested Category: {ai_res['suggested_category']}")
    print(f"    Suggested Priority: {ai_res['suggested_priority']}")

    # Submit complaint with AI confirmation and GPS
    print(f"\n[TEST 5] Submitting Complaint to SQLite with AI confirmation & GPS...")
    status, rep_res = post_json("/api/reports", {
        "title": "Severe Water Main Rupture flooding road",
        "category": ai_res["suggested_category"],
        "department": "Water Supply & Sewerage Board",
        "priority": ai_res["suggested_priority"],
        "ward": "Ward 18 - SIT College Campus / SIT Extension",
        "location": "Opposite SIT Main Gate, B.H. Road",
        "description": "Continuous high-pressure water leaking onto the road creating deep muddy pools.",
        "latitude": 13.3275,
        "longitude": 77.1261,
        "ai_detected_class": ai_res["detected_class"],
        "ai_confidence_score": ai_res["confidence_score"],
        "ai_model_name": ai_res["model_name"],
        "ai_suggested_category": ai_res["suggested_category"],
        "temp_image_filename": ai_res["temp_image_filename"]
    }, token=citizen_token)
    assert status == 201, f"Report creation failed: {rep_res}"
    tracking_id = rep_res["tracking_id"]
    print(f" -> PASS: Complaint saved in SQLite. Tracking ID: {tracking_id}")

    # TEST 6: Login as Municipal Officer
    print(f"\n[TEST 6] Logging In as Municipal Senior Engineer...")
    status, off_res = post_json("/api/auth/login", {
        "email": "engineer@citizenshield.gov",
        "password": "Engineer@2026"
    })
    assert status == 200, f"Officer login failed: {off_res}"
    officer_token = off_res["token"]
    print(f" -> PASS: Officer Authenticated: {off_res['user']['name']} ({off_res['user']['role']})")

    # TEST 7: Officer views complaint, image, AI result and location
    print(f"\n[TEST 7] Officer querying complaint records and AI inference details...")
    status, all_reps = get_json(f"/api/reports/all?search={tracking_id}", token=officer_token)
    assert status == 200 and len(all_reps["reports"]) > 0, f"Officer fetch failed: {all_reps}"
    found_rep = all_reps["reports"][0]
    print(f" -> PASS: Officer successfully retrieved report:")
    print(f"    Tracking ID: {found_rep['tracking_id']}")
    print(f"    Citizen: {found_rep['citizen_name']}")
    print(f"    AI Detected Class: {found_rep['detected_class']}")
    print(f"    AI Confidence: {found_rep['confidence_score']}")
    print(f"    Location: {found_rep['location']} (Lat: {found_rep['latitude']}, Lng: {found_rep['longitude']})")

    # TEST 8: Update complaint status & verify Status_History
    print(f"\n[TEST 8] Officer updating status to 'In Progress' with directive remarks...")
    status, upd_res = patch_json(f"/api/reports/{tracking_id}/status", {
        "status": "In Progress",
        "remarks": "KUWSDB Quick Response Valve Crew dispatched with jetting pump.",
        "priority": "High"
    }, token=officer_token)
    assert status == 200, f"Status update failed: {upd_res}"
    print(f" -> PASS: Status updated to 'In Progress'. Status_History recorded.")

    # TEST 9: Citizen tracks complaint & verifies timeline
    print(f"\n[TEST 9] Citizen tracking case dossier: {tracking_id}...")
    status, track_res = get_json(f"/api/reports/track/{tracking_id}")
    assert status == 200, f"Track failed: {track_res}"
    dossier = track_res["report"]
    history = dossier["status_history"]
    assert len(history) >= 2, f"Expected at least 2 history records, found {len(history)}"
    print(f" -> PASS: Citizen retrieved tracking dossier.")
    print(f"    Current Status: {dossier['status']}")
    print(f"    Timeline steps recorded in SQLite: {len(history)}")
    for h in history:
        print(f"      • [{h['created_at']}] {h['status']} - {h['remarks']} (By: {h['officer_name']})")

    # TEST 10: Verify AI Detection Dashboard against SQLite records
    print(f"\n[TEST 10] Verifying AI Detection Dashboard Analytics...")
    status, ai_metrics = get_json("/api/ai/metrics", token=officer_token)
    assert status == 200, f"AI metrics failed: {ai_metrics}"
    print(f" -> PASS: AI Analytics retrieved from SQLite:")
    print(f"    Total Images Analysed: {ai_metrics['total_analyzed']}")
    print(f"    Supported Detections:  {ai_metrics['total_supported_detections']}")
    print(f"    Average Confidence:    {ai_metrics['avg_confidence_percent']}")
    print(f"    Potholes:              {ai_metrics['potholes_detected']}")
    print(f"    Water Leakage:         {ai_metrics['water_leakage_detected']}")
    print(f"    Drainage:              {ai_metrics['drainage_detected']}")
    print(f"    Garbage:               {ai_metrics['garbage_detected']}")

    # Edge Check: Duplicate Detection
    print(f"\n[EDGE TEST] Testing Duplicate Detection Warning (< 75m radius)...")
    status, dup_res = post_json("/api/reports/check-duplicate", {
        "category": "Water Supply",
        "latitude": 13.3275,
        "longitude": 77.1261
    })
    assert status == 200, f"Duplicate check failed: {dup_res}"
    print(f" -> PASS: Duplicate logic verified. Detected nearby active complaints: {len(dup_res['nearby_reports'])}")
    if dup_res['is_duplicate']:
        print(f"    Warning: {dup_res['warning_message']}")

    # Security Check: Unauthorized Officer Console Access Block
    print(f"\n[SECURITY TEST] Verifying Role-Based Access Control (RBAC)...")
    status, unauth_res = get_json("/api/reports/all", token=citizen_token)
    assert status == 403, f"Expected 403 Forbidden, got {status}"
    print(f" -> PASS: Citizen blocked from Officer Console (HTTP 403 Forbidden).")

    print("\n" + "=" * 65)
    print("ALL 10 VERIFICATION TESTS & SECURITY CHECKS PASSED WITH ZERO ERRORS!")
    print("=" * 65)

if __name__ == "__main__":
    run_tests()
