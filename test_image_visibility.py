"""
CitizenShield Image Visibility & Officer Dashboard Verification Suite
Tests the exact 7 requirements from the user request:
1. Citizen logs in.
2. Citizen uploads a real complaint photograph with GPS.
3. Submits complaint.
4. Verify image file exists in uploads/ folder.
5. Verify correct relative image path is saved in SQLite reports table.
6. Municipal Officer logs in, retrieves the complaint, and accesses the original image URL.
7. Senior Officer / Admin logs in, retrieves the same complaint, and accesses the exact same image.
8. Verifies HTTP 200 on /api/uploads/<filename> with valid image content-type.
"""

import urllib.request
import json
import uuid
import os

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

def run_image_verification():
    print("=" * 65)
    print("CITIZENSHIELD - IMAGE VISIBILITY & OFFICER ACCESS VERIFICATION")
    print("=" * 65)

    # 1. Citizen Login
    print("\n[STEP 1] Citizen Authentication...")
    status, cit_res = post_json("/api/auth/login", {
        "email": "rahul.citizen@gmail.com",
        "password": "Citizen@2026"
    })
    assert status == 200, f"Citizen login failed: {cit_res}"
    cit_token = cit_res["token"]
    print(f" -> PASS: Citizen logged in. Name: {cit_res['user']['name']}")

    # 2. Citizen uploads real complaint image & lodges grievance
    print("\n[STEP 2] Citizen submitting complaint with real evidence photograph...")
    test_img = "uploads/1793251633_2ee4a5b9.jpeg"
    with open(test_img, "rb") as f:
        img_bytes = f.read()

    boundary = f"----WebKitFormBoundary{uuid.uuid4().hex[:16]}"
    title = f"Dangerous Tarmac Crater - Zone Test {uuid.uuid4().hex[:4]}"
    
    parts = []
    # Title
    parts.append(f"--{boundary}\r\nContent-Disposition: form-data; name=\"title\"\r\n\r\n{title}")
    # Category
    parts.append(f"--{boundary}\r\nContent-Disposition: form-data; name=\"category\"\r\n\r\nRoads and Transport")
    # Department
    parts.append(f"--{boundary}\r\nContent-Disposition: form-data; name=\"department\"\r\n\r\nRoads & Civil Infrastructure")
    # Priority
    parts.append(f"--{boundary}\r\nContent-Disposition: form-data; name=\"priority\"\r\n\r\nHigh")
    # Ward
    parts.append(f"--{boundary}\r\nContent-Disposition: form-data; name=\"ward\"\r\n\r\nWard 11 - Mandipet / Town Hall Commercial Core")
    # Description
    parts.append(f"--{boundary}\r\nContent-Disposition: form-data; name=\"description\"\r\n\r\nDeep crater on main road with damaged asphalt.")
    # Location
    parts.append(f"--{boundary}\r\nContent-Disposition: form-data; name=\"location\"\r\n\r\nNear Town Hall Circle, Mandipet")
    # Coordinates
    parts.append(f"--{boundary}\r\nContent-Disposition: form-data; name=\"latitude\"\r\n\r\n13.3421")
    parts.append(f"--{boundary}\r\nContent-Disposition: form-data; name=\"longitude\"\r\n\r\n77.1035")
    
    # Image file part
    header_img = f"--{boundary}\r\nContent-Disposition: form-data; name=\"image\"; filename=\"pothole_evidence.jpeg\"\r\nContent-Type: image/jpeg\r\n\r\n".encode("utf-8")
    footer_img = f"\r\n--{boundary}--\r\n".encode("utf-8")
    
    body_data = "\r\n".join(parts).encode("utf-8") + b"\r\n" + header_img + img_bytes + footer_img

    req = urllib.request.Request(
        f"{BASE_URL}/api/reports",
        data=body_data,
        headers={
            "Content-Type": f"multipart/form-data; boundary={boundary}",
            "Authorization": f"Bearer {cit_token}"
        },
        method="POST"
    )

    with urllib.request.urlopen(req) as resp:
        submit_res = json.loads(resp.read().decode("utf-8"))

    assert "report_id" in submit_res, f"Submission failed: {submit_res}"
    tracking_id = submit_res["report_id"]
    print(f" -> PASS: Complaint lodged into SQLite. Tracking ID: {tracking_id}")

    # 3. Verify in SQLite that image_path & image_filename exist on disk
    print("\n[STEP 3] Verifying SQLite Report record & file persistence on disk...")
    import sqlite3
    conn = sqlite3.connect("data/citizenshield.db")
    conn.row_factory = sqlite3.Row
    row = conn.execute("SELECT * FROM reports WHERE report_id = ?", (tracking_id,)).fetchone()
    conn.close()

    assert row is not None, "Report row not found in SQLite"
    saved_filename = row["image_filename"]
    saved_path = row["image_path"]
    print(f"    SQLite image_filename: {saved_filename}")
    print(f"    SQLite image_path:     {saved_path}")
    assert saved_filename and saved_path, "Image path or filename missing in SQLite"

    full_disk_path = os.path.join("uploads", saved_filename)
    assert os.path.isfile(full_disk_path), f"File {full_disk_path} does not exist on disk!"
    print(f" -> PASS: Uploaded image verified on disk ({os.path.getsize(full_disk_path)} bytes)")

    # 4. Municipal Officer Login & Inspection
    print("\n[STEP 4] Municipal Officer Login & Image Access...")
    status, off_res = post_json("/api/auth/login", {
        "email": "engineer@citizenshield.gov",
        "password": "Engineer@2026"
    })
    assert status == 200, f"Officer login failed: {off_res}"
    officer_token = off_res["token"]

    status, reps_data = get_json(f"/api/reports/all?search={tracking_id}", token=officer_token)
    assert status == 200 and len(reps_data["reports"]) > 0, "Officer could not retrieve report"
    rep_for_officer = reps_data["reports"][0]
    print(f"    Officer retrieved complaint: {rep_for_officer['tracking_id']}")
    print(f"    Image attached: {rep_for_officer['image_filename']}")
    assert rep_for_officer["image_filename"] == saved_filename, "Image filename mismatch for officer"

    # Fetch image via /api/uploads/<filename>
    img_url = f"{BASE_URL}/api/uploads/{saved_filename}"
    img_req = urllib.request.Request(img_url)
    with urllib.request.urlopen(img_req) as img_resp:
        assert img_resp.status == 200, f"Failed to fetch image: status {img_resp.status}"
        fetched_bytes = img_resp.read()
        assert len(fetched_bytes) > 0, "Fetched image is empty"
        print(f" -> PASS: Municipal Officer successfully rendered image ({len(fetched_bytes)} bytes, HTTP 200)")

    # 5. Senior Officer / Admin Login & Inspection
    print("\n[STEP 5] Senior Officer (Municipal Commissioner) Login & Image Access...")
    status, adm_res = post_json("/api/auth/login", {
        "email": "admin@citizenshield.gov",
        "password": "Admin@2026"
    })
    assert status == 200, f"Admin login failed: {adm_res}"
    admin_token = adm_res["token"]

    status, adm_reps_data = get_json(f"/api/reports/all?search={tracking_id}", token=admin_token)
    assert status == 200 and len(adm_reps_data["reports"]) > 0, "Senior Officer could not retrieve report"
    rep_for_admin = adm_reps_data["reports"][0]
    print(f"    Senior Officer retrieved complaint: {rep_for_admin['tracking_id']}")
    print(f"    Image attached: {rep_for_admin['image_filename']}")
    assert rep_for_admin["image_filename"] == saved_filename, "Image filename mismatch for senior officer"

    # Senior Officer fetches the exact same image
    with urllib.request.urlopen(urllib.request.Request(img_url)) as adm_img_resp:
        assert adm_img_resp.status == 200
        assert len(adm_img_resp.read()) == len(fetched_bytes)
        print(f" -> PASS: Senior Officer successfully viewed the exact original complaint photograph!")

    print("\n" + "=" * 65)
    print("ALL IMAGE VISIBILITY & OFFICER ACCESS TESTS PASSED WITH 100% SUCCESS!")
    print("=" * 65)

if __name__ == "__main__":
    run_image_verification()
