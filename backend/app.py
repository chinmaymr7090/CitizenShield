# CitizenShield - Robust Municipal Backend Server
import os
import uuid
import secrets
import math
from datetime import datetime, timezone, timedelta
from functools import wraps
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from werkzeug.utils import secure_filename
import sys

# Ensure backend directory is in sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import (
    get_connection,
    init_db,
    hash_password,
    verify_password,
    DB_PATH
)
from ai_engine import analyze_civic_image

# App Configuration
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
UPLOADS_DIR = os.path.join(BASE_DIR, "uploads")
STATIC_DIR = os.path.join(BASE_DIR, "static")

os.makedirs(UPLOADS_DIR, exist_ok=True)
os.makedirs(STATIC_DIR, exist_ok=True)

app = Flask(__name__, static_folder=STATIC_DIR, static_url_path="/static")
CORS(app)
app.config['MAX_CONTENT_LENGTH'] = 15 * 1024 * 1024  # 15 MB Max upload
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp', 'gif'}

# Initialize database on startup
init_db()

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def calculate_haversine_distance(lat1, lon1, lat2, lon2):
    """Calculates distance in meters between two GPS coordinates."""
    if lat1 is None or lon1 is None or lat2 is None or lon2 is None:
        return float('inf')
    R = 6371000  # Earth radius in meters
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)
    a = math.sin(delta_phi / 2)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

def suggest_priority_rule(title, description, category, detected_class=None):
    """
    Transparent rule-based priority classifier.
    Categorizes complaints into Urgent, High, and Normal based on civic severity.
    """
    text = f"{title} {description} {category} {detected_class or ''}".lower()
    urgent_keywords = ["danger", "hazard", "electrical", "spark", "blackout", "live wire", "burst", "flood", "sewage overflow", "cave in", "sinkhole"]
    high_keywords = ["pothole", "accident", "crater", "drainage", "water leak", "pipeline", "stagnant", "traffic block"]

    for kw in urgent_keywords:
        if kw in text:
            return "Urgent", f"Classified as Urgent due to critical safety keyword: '{kw}'"

    for kw in high_keywords:
        if kw in text:
            return "High", f"Classified as High priority due to infrastructural risk keyword: '{kw}'"

    return "Normal", "Standard priority queue (Normal) based on municipal SLA rules"

def get_current_user():
    """Extracts and verifies the bearer token from the request."""
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        return None
    token = auth_header.split(" ", 1)[1].strip()
    if not token:
        return None

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT u.id, u.user_id, u.uuid, u.name, u.email, u.role, u.department, u.phone
        FROM auth_tokens t
        JOIN users u ON t.user_id = u.id
        WHERE t.token = ? AND t.expires_at > CURRENT_TIMESTAMP
    """, (token,))
    row = cursor.fetchone()
    conn.close()
    if not row:
        return None
    return dict(row)

def require_auth(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user = get_current_user()
        if not user:
            return jsonify({"error": "Unauthorized. Active municipal credentials required."}), 401
        return f(user, *args, **kwargs)
    return decorated_function

def require_admin(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user = get_current_user()
        if not user:
            return jsonify({"error": "Authentication required."}), 401
        if user.get("role") not in ["admin", "officer", "engineer"]:
            return jsonify({"error": "Access denied. Municipal Directorate authorization required."}), 403
        return f(user, *args, **kwargs)
    return decorated_function

def log_audit(event_type, details, user_email="Anonymous"):
    try:
        conn = get_connection()
        ip = request.remote_addr or "127.0.0.1"
        now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
        conn.execute("""
            INSERT INTO audit_logs (event_type, action, user_email, details, ip_address, timestamp, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (event_type, event_type, user_email, details, ip, now_str, now_str))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"[Audit Log Error] {e}")

# ==========================================================
# PUBLIC & HEALTH ENDPOINTS
# ==========================================================

@app.route("/api/health", methods=["GET"])
def health_check():
    return jsonify({
        "status": "HEALTHY",
        "service": "CitizenShield Smart Grievance Engine",
        "database": "SQLite (Persistent)",
        "ai_engine": "YOLOv8 & OpenCV Computer Vision Active",
        "timestamp": datetime.now(timezone.utc).isoformat()
    })

# ==========================================================
# AUTHENTICATION ENDPOINTS
# ==========================================================

@app.route("/api/auth/register", methods=["POST"])
def register():
    data = request.get_json(silent=True) or {}
    name = (data.get("name") or "").strip()
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""
    phone = (data.get("phone") or "").strip()
    role = (data.get("role") or "citizen").strip().lower()

    if not name or not email or not password:
        return jsonify({"error": "Name, valid email, and password are required."}), 400

    if len(password) < 6:
        return jsonify({"error": "Password must be at least 6 characters long."}), 400

    if role not in ["citizen", "admin", "officer"]:
        role = "citizen"

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT id FROM users WHERE email = ?", (email,))
    if cursor.fetchone():
        conn.close()
        return jsonify({"error": "An account with this email address already exists."}), 409

    pwd_hash, salt = hash_password(password)
    user_uuid = str(uuid.uuid4())

    cursor.execute("""
        INSERT INTO users (uuid, name, email, phone, password_hash, password_salt, role, department)
        VALUES (?, ?, ?, ?, ?, ?, ?, 'General Public')
    """, (user_uuid, name, email, phone, pwd_hash, salt, role))

    new_id = cursor.lastrowid
    cursor.execute("UPDATE users SET user_id = ? WHERE id = ?", (new_id, new_id))
    conn.commit()
    conn.close()

    log_audit("USER_REGISTERED", f"New user registered: {email} ({role})", email)

    return jsonify({
        "message": "Citizen registration successful. You may now sign in.",
        "user_id": new_id,
        "email": email
    }), 201

@app.route("/api/auth/login", methods=["POST"])
def login():
    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""

    if not email or not password:
        return jsonify({"error": "Email and password are required."}), 400

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, user_id, uuid, name, email, password_hash, password_salt, role, department, phone
        FROM users
        WHERE email = ?
    """, (email,))
    user = cursor.fetchone()

    if not user or not verify_password(password, user["password_salt"], user["password_hash"]):
        conn.close()
        log_audit("LOGIN_FAILED", f"Invalid credentials attempt for: {email}", email)
        return jsonify({"error": "Invalid email or password credentials."}), 401

    token = secrets.token_hex(32)
    expires_at = datetime.now(timezone.utc) + timedelta(days=7)

    cursor.execute("""
        INSERT INTO auth_tokens (token, user_id, expires_at)
        VALUES (?, ?, ?)
    """, (token, user["id"], expires_at.strftime("%Y-%m-%d %H:%M:%S")))
    conn.commit()
    conn.close()

    log_audit("LOGIN_SUCCESS", f"User logged in: {email} ({user['role']})", email)

    return jsonify({
        "token": token,
        "user": {
            "id": user["id"],
            "user_id": user["user_id"] or user["id"],
            "uuid": user["uuid"],
            "name": user["name"],
            "email": user["email"],
            "role": user["role"],
            "department": user["department"],
            "phone": user["phone"]
        }
    })

@app.route("/api/auth/me", methods=["GET"])
@require_auth
def get_profile(user):
    return jsonify({"user": user})

@app.route("/api/auth/logout", methods=["POST"])
def logout():
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        token = auth_header.split(" ", 1)[1].strip()
        conn = get_connection()
        conn.execute("DELETE FROM auth_tokens WHERE token = ?", (token,))
        conn.commit()
        conn.close()
    return jsonify({"message": "Successfully logged out."})

# ==========================================================
# MODULE 2: REAL AI IMAGE DETECTION ENDPOINT
# ==========================================================

@app.route("/api/ai/analyze-image", methods=["POST"])
def ai_analyze_image():
    """
    Real AI Civic Image Inspection.
    Validates uploaded image and runs real inference via YOLOv8 & OpenCV.
    Returns detected class, confidence score, suggested category, and suggested priority.
    """
    if "image" not in request.files:
        return jsonify({"error": "No image file provided in request."}), 400

    file = request.files["image"]
    if not file or not file.filename:
        return jsonify({"error": "Empty filename."}), 400

    if not allowed_file(file.filename):
        return jsonify({"error": "Unsupported file format. Please upload PNG, JPG, JPEG, or WEBP."}), 400

    ext = file.filename.rsplit('.', 1)[1].lower()
    temp_name = f"temp_ai_{int(datetime.now().timestamp())}_{uuid.uuid4().hex[:8]}.{ext}"
    temp_path = os.path.join(UPLOADS_DIR, temp_name)
    file.save(temp_path)

    # Run actual AI inference
    result = analyze_civic_image(temp_path)
    result["temp_image_filename"] = temp_name

    return jsonify(result)

# ==========================================================
# MODULE 7: DUPLICATE COMPLAINT DETECTION ENDPOINT
# ==========================================================

@app.route("/api/reports/check-duplicate", methods=["POST"])
def check_duplicate():
    """
    Checks if an active complaint in the same category exists within 50 meters.
    Transparent warning mechanism without auto-deletion.
    """
    data = request.get_json(silent=True) or {}
    category = data.get("category")
    lat = data.get("latitude")
    lng = data.get("longitude")

    if lat is None or lng is None or not category:
        return jsonify({"is_duplicate": False, "nearby_reports": []})

    try:
        lat = float(lat)
        lng = float(lng)
    except ValueError:
        return jsonify({"is_duplicate": False, "nearby_reports": []})

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT report_id, tracking_id, title, category, latitude, longitude, status, created_at
        FROM reports
        WHERE status IN ('Submitted', 'Under Review', 'In Progress', 'Dispatched')
          AND latitude IS NOT NULL AND longitude IS NOT NULL
    """)
    active_reports = cursor.fetchall()
    conn.close()

    nearby = []
    for r in active_reports:
        dist = calculate_haversine_distance(lat, lng, r["latitude"], r["longitude"])
        if dist <= 75.0:  # Within 75 meters
            is_same_cat = (r["category"].lower().strip() == category.lower().strip())
            nearby.append({
                "report_id": r["report_id"],
                "tracking_id": r["tracking_id"] or r["report_id"],
                "title": r["title"],
                "category": r["category"],
                "status": r["status"],
                "distance_meters": round(dist, 1),
                "same_category": is_same_cat,
                "created_at": r["created_at"]
            })

    duplicate_found = any(n["same_category"] for n in nearby)

    return jsonify({
        "is_duplicate": duplicate_found,
        "warning_message": "A similar active complaint was reported within 75 meters of this location." if duplicate_found else None,
        "nearby_reports": nearby
    })

# ==========================================================
# MODULE 4 & 5: REPORT REGISTRATION & MANAGEMENT
# ==========================================================

@app.route("/api/reports", methods=["POST"])
@require_auth
def create_report(user):
    if request.content_type and "multipart/form-data" in request.content_type:
        form = request.form
        files = request.files
    else:
        form = request.get_json(silent=True) or {}
        files = {}

    title = (form.get("title") or form.get("complaint_title") or "").strip()
    category = (form.get("category") or "").strip()
    department = (form.get("department") or "Roads & Civil Infrastructure").strip()
    priority = (form.get("priority") or "Normal").strip()
    description = (form.get("description") or "").strip()
    location = (form.get("location") or "").strip()
    ward = (form.get("ward") or "Ward 11 - Mandipet / Town Hall Division").strip()

    lat = form.get("latitude")
    lng = form.get("longitude")
    latitude = float(lat) if lat and str(lat).strip() else None
    longitude = float(lng) if lng and str(lng).strip() else None

    # AI Detection result fields submitted from frontend
    ai_detected_class = form.get("ai_detected_class")
    ai_confidence = form.get("ai_confidence_score")
    ai_model = form.get("ai_model_name") or "YOLOv8-Ensemble-v1"
    ai_suggested_cat = form.get("ai_suggested_category")
    existing_temp_image = form.get("temp_image_filename")

    if not title or not category or not description or not location:
        return jsonify({"error": "Title, Category, Description, and Location are mandatory."}), 400

    # Handle image upload or finalize previously uploaded temp image
    image_filename = None
    if "image" in files:
        file = files["image"]
        if file and file.filename and allowed_file(file.filename):
            ext = file.filename.rsplit('.', 1)[1].lower()
            unique_name = f"{int(datetime.now().timestamp())}_{uuid.uuid4().hex[:8]}.{ext}"
            saved_path = os.path.join(UPLOADS_DIR, unique_name)
            file.save(saved_path)
            image_filename = unique_name

            # If AI was not run on client, run AI analysis automatically now
            if not ai_detected_class:
                ai_res = analyze_civic_image(saved_path)
                if ai_res.get("detected"):
                    ai_detected_class = ai_res.get("detected_class")
                    ai_confidence = ai_res.get("confidence_score")
                    ai_model = ai_res.get("model_name")
                    ai_suggested_cat = ai_res.get("suggested_category")
    elif existing_temp_image:
        temp_path = os.path.join(UPLOADS_DIR, existing_temp_image)
        if os.path.exists(temp_path):
            image_filename = existing_temp_image

    # Generate unique Tracking ID (CS-2026-XXXXX)
    year = datetime.now().year
    random_num = secrets.randbelow(90000) + 10000
    report_id = f"CS-{year}-{random_num}"
    tracking_id = report_id

    # Rule-based priority check if priority was not explicitly overridden
    if priority == "Normal":
        suggested_prio, _ = suggest_priority_rule(title, description, category, ai_detected_class)
        priority = suggested_prio

    sla_map = {"Urgent": 12, "High": 24, "Normal": 48, "Low": 72}
    sla_hours = sla_map.get(priority, 48)
    now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO reports (
            report_id, tracking_id, user_id, citizen_name, citizen_email, citizen_phone,
            title, complaint_title, category, department, priority, description, location,
            ward, latitude, longitude, image_filename, image_path, status, admin_remarks,
            sla_hours, created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'Submitted', '', ?, ?, ?)
    """, (
        report_id, tracking_id, user["id"], user["name"], user["email"], user.get("phone", ""),
        title, title, category, department, priority, description, location,
        ward, latitude, longitude, image_filename, image_filename, sla_hours,
        now_str, now_str
    ))

    # Record AI Detection result in ai_detections table
    if ai_detected_class and ai_confidence:
        try:
            conf_val = float(ai_confidence)
        except ValueError:
            conf_val = 0.0
        cursor.execute("""
            INSERT INTO ai_detections (
                report_id, detected_class, confidence_score, model_name,
                suggested_category, citizen_confirmed_category, detection_status, detected_at
            ) VALUES (?, ?, ?, ?, ?, ?, 'SUCCESS', ?)
        """, (
            report_id, ai_detected_class, conf_val, ai_model,
            ai_suggested_cat or category, category, now_str
        ))
    else:
        # Record detection failure or manual submission
        cursor.execute("""
            INSERT INTO ai_detections (
                report_id, detected_class, confidence_score, model_name,
                suggested_category, citizen_confirmed_category, detection_status, detected_at
            ) VALUES (?, 'No supported civic problem detected', 0.0, 'YOLOv8-Ensemble-v1',
                      'Manual Selection', ?, 'MANUAL_FALLBACK', ?)
        """, (report_id, category, now_str))

    # Initial status history entry
    cursor.execute("""
        INSERT INTO status_history (
            report_id, previous_status, new_status, status, remarks, officer_remarks,
            officer_name, officer_role, updated_by, created_at, updated_at
        ) VALUES (?, '', 'Submitted', 'Submitted', 'Official grievance lodged via citizen portal.',
                  'Official grievance lodged via citizen portal.', 'Citizen Submitter', 'Citizen',
                  'Citizen Submitter', ?, ?)
    """, (report_id, now_str, now_str))

    conn.commit()
    conn.close()

    log_audit("REPORT_CREATED", f"Grievance {report_id} registered: {title} ({category})", user["email"])

    return jsonify({
        "message": "Grievance successfully recorded in municipal registry.",
        "report_id": report_id,
        "tracking_id": tracking_id,
        "status": "Submitted",
        "priority": priority,
        "ai_detection": {
            "detected_class": ai_detected_class,
            "confidence_score": ai_confidence,
            "model_name": ai_model
        } if ai_detected_class else None
    }), 201

@app.route("/api/reports/my", methods=["GET"])
@require_auth
def get_my_reports(user):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT r.*,
               a.detected_class, a.confidence_score, a.model_name
        FROM reports r
        LEFT JOIN ai_detections a ON r.report_id = a.report_id
        WHERE r.user_id = ?
        ORDER BY r.created_at DESC
    """, (user["id"],))
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return jsonify({"reports": rows})

@app.route("/api/reports/track/<report_id>", methods=["GET"])
def track_report(report_id):
    clean_id = (report_id or "").strip().upper()
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT r.*,
               a.detected_class, a.confidence_score, a.model_name, a.suggested_category
        FROM reports r
        LEFT JOIN ai_detections a ON r.report_id = a.report_id
        WHERE r.report_id = ? OR r.tracking_id = ?
    """, (clean_id, clean_id))
    report = cursor.fetchone()
    if not report:
        conn.close()
        return jsonify({"error": f"No municipal record found for Tracking ID: {clean_id}"}), 404

    report_dict = dict(report)

    # Privacy and Authorization Check if user is logged in
    current_usr = get_current_user()
    if current_usr:
        # If user is citizen and not admin/officer, they can only track their own complaints
        if current_usr.get("role") not in ["admin", "officer", "engineer"] and report_dict.get("user_id"):
            if current_usr["id"] != report_dict["user_id"]:
                conn.close()
                return jsonify({"error": "Access Denied: You are not authorized to view grievance details registered by another citizen."}), 403

    cursor.execute("""
        SELECT status, new_status, remarks, officer_remarks, officer_name, officer_role, updated_by, created_at
        FROM status_history
        WHERE report_id = ?
        ORDER BY created_at ASC
    """, (report_dict["report_id"],))
    history = [dict(h) for h in cursor.fetchall()]
    report_dict["status_history"] = history

    # Fetch Officer Replies
    cursor.execute("""
        SELECT reply_id, report_id, officer_id, officer_name, officer_role, reply_message,
               previous_status, new_status, resolution_details, after_repair_image, created_at
        FROM officer_replies
        WHERE report_id = ?
        ORDER BY created_at DESC
    """, (report_dict["report_id"],))
    replies = [dict(rep) for rep in cursor.fetchall()]
    report_dict["officer_replies"] = replies

    conn.close()
    return jsonify({"report": report_dict})

@app.route("/api/reports/all", methods=["GET"])
@require_admin
def get_all_reports(user):
    status = request.args.get("status")
    category = request.args.get("category")
    priority = request.args.get("priority")
    search = request.args.get("search", "").strip()

    query = """
        SELECT r.*,
               a.detected_class, a.confidence_score, a.model_name, a.detection_status
        FROM reports r
        LEFT JOIN ai_detections a ON r.report_id = a.report_id
        WHERE 1=1
    """
    params = []

    if status and status != "ALL":
        query += " AND r.status = ?"
        params.append(status)

    if category and category != "ALL":
        query += " AND r.category = ?"
        params.append(category)

    if priority and priority != "ALL":
        query += " AND r.priority = ?"
        params.append(priority)

    if search:
        query += " AND (r.report_id LIKE ? OR r.tracking_id LIKE ? OR r.title LIKE ? OR r.citizen_name LIKE ? OR r.location LIKE ?)"
        like_term = f"%{search}%"
        params.extend([like_term, like_term, like_term, like_term, like_term])

    query += " ORDER BY r.created_at DESC"

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(query, params)
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()

    return jsonify({"reports": rows})

@app.route("/api/reports/map", methods=["GET"])
def get_map_reports():
    """Returns geotagged reports for the interactive Leaflet GIS map."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT r.report_id, r.tracking_id, r.title, r.category, r.department, r.priority, r.status,
               r.location, r.ward, r.latitude, r.longitude, r.image_filename, r.created_at,
               a.detected_class, a.confidence_score
        FROM reports r
        LEFT JOIN ai_detections a ON r.report_id = a.report_id
        WHERE r.latitude IS NOT NULL AND r.longitude IS NOT NULL
        ORDER BY r.created_at DESC
    """)
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return jsonify({"pins": rows})

@app.route("/api/reports/<report_id>/status", methods=["PATCH"])
@require_admin
def update_report_status(user, report_id):
    clean_id = (report_id or "").strip().upper()
    
    # Handle multipart for after-repair photo or standard JSON
    if request.content_type and "multipart/form-data" in request.content_type:
        form = request.form
        files = request.files
    else:
        form = request.get_json(silent=True) or {}
        files = {}

    new_status = form.get("status")
    remarks = (form.get("remarks") or "").strip()
    department = form.get("department")
    priority = form.get("priority")

    valid_statuses = ["Submitted", "Under Review", "Dispatched", "In Progress", "Resolved", "Rejected"]
    if not new_status or new_status not in valid_statuses:
        return jsonify({"error": f"Invalid status. Must be one of: {', '.join(valid_statuses)}"}), 400

    if not remarks:
        return jsonify({"error": "Administrative justification and action remarks are mandatory."}), 400

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT id, user_id, status, title, after_repair_image FROM reports WHERE report_id = ? OR tracking_id = ?", (clean_id, clean_id))
    report = cursor.fetchone()
    if not report:
        conn.close()
        return jsonify({"error": "Report not found."}), 404

    current_status = report["status"]
    after_image_name = report["after_repair_image"]

    # Module 5 Enforcement: Require an after-repair photograph before marking as Resolved
    if new_status == "Resolved":
        if "after_image" in files:
            a_file = files["after_image"]
            if a_file and a_file.filename and allowed_file(a_file.filename):
                ext = a_file.filename.rsplit('.', 1)[1].lower()
                after_image_name = f"resolved_{int(datetime.now().timestamp())}_{uuid.uuid4().hex[:8]}.{ext}"
                a_file.save(os.path.join(UPLOADS_DIR, after_image_name))
        
        if not after_image_name:
            conn.close()
            return jsonify({
                "error": "Statutory Requirement: An after-repair verification photograph and remarks are strictly required before marking a civic defect as Resolved."
            }), 400

    now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")

    cursor.execute("""
        UPDATE reports
        SET status = ?, admin_remarks = ?, after_repair_image = ?,
            department = COALESCE(?, department),
            priority = COALESCE(?, priority),
            updated_at = ?
        WHERE report_id = ? OR tracking_id = ?
    """, (new_status, remarks, after_image_name, department or None, priority or None, now_str, clean_id, clean_id))

    # Append to status_history
    cursor.execute("""
        INSERT INTO status_history (
            report_id, previous_status, new_status, status, remarks, officer_remarks,
            officer_name, officer_role, updated_by, created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        clean_id, current_status, new_status, new_status, remarks, remarks,
        user["name"], user.get("role", "Officer").title(), user["name"],
        now_str, now_str
    ))

    # Module 2 & 4: Record Officer Reply and Notify Citizen
    cursor.execute("""
        INSERT INTO officer_replies (
            report_id, officer_id, officer_name, officer_role, reply_message,
            previous_status, new_status, resolution_details, after_repair_image, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        clean_id, user["id"], user["name"], user.get("role", "Officer").title(),
        remarks, current_status, new_status,
        remarks if new_status == "Resolved" else None,
        after_image_name if new_status == "Resolved" else None,
        now_str
    ))

    # Send in-app notification to the citizen
    if report["user_id"]:
        notif_title = f"Official Directive: {clean_id} is now {new_status}"
        notif_msg = f"{user['name']} issued an update: {remarks[:140]}"
        cursor.execute("""
            INSERT INTO notifications (user_id, report_id, title, message, is_read, created_at)
            VALUES (?, ?, ?, ?, 0, ?)
        """, (report["user_id"], clean_id, notif_title, notif_msg, now_str))

    conn.commit()
    conn.close()

    log_audit("STATUS_UPDATED", f"{clean_id} changed from {current_status} to {new_status} by {user['name']}: {remarks}", user["email"])

    return jsonify({
        "message": f"Report {clean_id} updated to {new_status}.",
        "report_id": clean_id,
        "previous_status": current_status,
        "status": new_status,
        "remarks": remarks,
        "after_repair_image": after_image_name
    })

# ==========================================================
# MODULE 2 & 4: DEDICATED OFFICER REPLY & NOTIFICATIONS API
# ==========================================================

@app.route("/api/reports/<report_id>/reply", methods=["POST"])
@require_admin
def reply_to_citizen(user, report_id):
    """
    Dedicated endpoint for Municipal Officers to send official replies to citizens.
    Supports official replies, status transitions, department reassignment,
    inspection remarks, and post-repair photographic verification.
    """
    clean_id = (report_id or "").strip().upper()
    
    if request.content_type and "multipart/form-data" in request.content_type:
        form = request.form
        files = request.files
    else:
        form = request.get_json(silent=True) or {}
        files = {}

    reply_message = (form.get("reply_message") or form.get("remarks") or "").strip()
    new_status = form.get("new_status") or form.get("status")
    department = form.get("department")
    priority = form.get("priority")
    resolution_details = (form.get("resolution_details") or "").strip()

    if not reply_message:
        return jsonify({"error": "Mandatory: Please enter an official reply message for the citizen."}), 400

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT id, user_id, status, title, department, priority, after_repair_image FROM reports WHERE report_id = ? OR tracking_id = ?", (clean_id, clean_id))
    report = cursor.fetchone()
    if not report:
        conn.close()
        return jsonify({"error": f"No municipal complaint found for reference {clean_id}."}), 404

    current_status = report["status"]
    status_to_set = new_status if new_status and new_status in ["Submitted", "Under Review", "Dispatched", "In Progress", "Resolved", "Rejected"] else current_status
    after_image_name = report["after_repair_image"]

    if status_to_set == "Resolved":
        if "after_image" in files:
            a_file = files["after_image"]
            if a_file and a_file.filename and allowed_file(a_file.filename):
                ext = a_file.filename.rsplit('.', 1)[1].lower()
                after_image_name = f"resolved_{int(datetime.now().timestamp())}_{uuid.uuid4().hex[:8]}.{ext}"
                a_file.save(os.path.join(UPLOADS_DIR, after_image_name))
        
        if not after_image_name:
            conn.close()
            return jsonify({
                "error": "Statutory Requirement: An after-repair verification photograph is strictly required before marking a civic defect as Resolved."
            }), 400

    now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")

    # Update reports table
    cursor.execute("""
        UPDATE reports
        SET status = ?, admin_remarks = ?, after_repair_image = ?,
            department = COALESCE(?, department),
            priority = COALESCE(?, priority),
            updated_at = ?
        WHERE report_id = ? OR tracking_id = ?
    """, (status_to_set, reply_message, after_image_name, department or None, priority or None, now_str, clean_id, clean_id))

    # Insert into officer_replies
    cursor.execute("""
        INSERT INTO officer_replies (
            report_id, officer_id, officer_name, officer_role, reply_message,
            previous_status, new_status, resolution_details, after_repair_image, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        clean_id, user["id"], user["name"], user.get("role", "Officer").title(),
        reply_message, current_status, status_to_set,
        resolution_details or (reply_message if status_to_set == "Resolved" else None),
        after_image_name if status_to_set == "Resolved" else None,
        now_str
    ))

    # Append to status_history if status changed or remarks issued
    cursor.execute("""
        INSERT INTO status_history (
            report_id, previous_status, new_status, status, remarks, officer_remarks,
            officer_name, officer_role, updated_by, created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        clean_id, current_status, status_to_set, status_to_set, reply_message, reply_message,
        user["name"], user.get("role", "Officer").title(), user["name"],
        now_str, now_str
    ))

    # Create citizen notification
    if report["user_id"]:
        notif_title = f"Official Reply on {clean_id}: {status_to_set}"
        notif_msg = f"{user['name']}: {reply_message[:140]}"
        cursor.execute("""
            INSERT INTO notifications (user_id, report_id, title, message, is_read, created_at)
            VALUES (?, ?, ?, ?, 0, ?)
        """, (report["user_id"], clean_id, notif_title, notif_msg, now_str))

    conn.commit()
    conn.close()

    log_audit("OFFICER_REPLY_SENT", f"Officer {user['name']} replied to {clean_id} (Status: {status_to_set}): {reply_message}", user["email"])

    return jsonify({
        "message": "Official Directive & Reply Published Successfully.",
        "report_id": clean_id,
        "previous_status": current_status,
        "new_status": status_to_set,
        "reply_message": reply_message,
        "officer_name": user["name"],
        "after_repair_image": after_image_name
    })

@app.route("/api/reports/<report_id>/replies", methods=["GET"])
def get_report_replies(report_id):
    clean_id = (report_id or "").strip().upper()
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT reply_id, report_id, officer_id, officer_name, officer_role, reply_message,
               previous_status, new_status, resolution_details, after_repair_image, created_at
        FROM officer_replies
        WHERE report_id = ?
        ORDER BY created_at DESC
    """, (clean_id,))
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return jsonify({"replies": rows})

@app.route("/api/notifications", methods=["GET"])
@require_auth
def get_user_notifications(user):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, report_id, title, message, is_read, created_at
        FROM notifications
        WHERE user_id = ?
        ORDER BY created_at DESC
        LIMIT 50
    """, (user["id"],))
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return jsonify({"notifications": rows})

@app.route("/api/notifications/<int:notif_id>/read", methods=["POST"])
@require_auth
def mark_notification_read(user, notif_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE notifications SET is_read = 1 WHERE id = ? AND user_id = ?", (notif_id, user["id"]))
    conn.commit()
    conn.close()
    return jsonify({"success": True})

# ==========================================================
# MODULE: LIVE COLOUR-CODED COMPLAINT ZONE MONITORING
# ==========================================================

# 6 Officially demarcated Tumakuru City Corporation Sectors / Geographical Zones
MUNICIPAL_ZONES = [
    {
        "id": "ZONE-CENTRAL",
        "name": "Zone 1 - Central Commercial Core",
        "description": "Town Hall, Mandipet, Chickpet, Ashok Nagar, Market Corridor",
        "bounds": [[13.3350, 77.0950], [13.3500, 77.1150]],
        "center": [13.3425, 77.1050],
        "assigned_department": "Roads & Civil Infrastructure"
    },
    {
        "id": "ZONE-EAST-SIT",
        "name": "Zone 2 - East SIT & Institutional Corridor",
        "description": "SIT College Campus, SIT Extension, Vidyanagar, B.H. Road East",
        "bounds": [[13.3200, 77.1150], [13.3350, 77.1350]],
        "center": [13.3275, 77.1250],
        "assigned_department": "Water Supply & Sewerage Board"
    },
    {
        "id": "ZONE-SOUTH-EAST",
        "name": "Zone 3 - South-East Gateway & Siddaganga Hub",
        "description": "Kyatsandra, Siddaganga Math Gateway, Batawadi South, Highway Bypass",
        "bounds": [[13.2900, 77.1350], [13.3250, 77.1700]],
        "center": [13.3075, 77.1525],
        "assigned_department": "Electrical & Public Lighting"
    },
    {
        "id": "ZONE-NORTH",
        "name": "Zone 4 - North Industrial & Sira Corridor",
        "description": "Antharasanahalli, Sira Road North, Maralenahalli, Belagumba",
        "bounds": [[13.3500, 77.0850], [13.3750, 77.1250]],
        "center": [13.3625, 77.1050],
        "assigned_department": "Solid Waste Management Cell"
    },
    {
        "id": "ZONE-WEST",
        "name": "Zone 5 - West Railway & Market Sector",
        "description": "Gubbi Gate Market, Railway Station Corridor, Heggere West, Melekote",
        "bounds": [[13.3300, 77.0750], [13.3500, 77.0950]],
        "center": [13.3400, 77.0850],
        "assigned_department": "Roads & Civil Infrastructure"
    },
    {
        "id": "ZONE-SOUTH-RESIDENTIAL",
        "name": "Zone 6 - South Residential & Lake Promenade",
        "description": "SS Puram, Upparhalli, Amanikere Lake Promenade, Saraswathipuram",
        "bounds": [[13.3150, 77.0850], [13.3350, 77.1150]],
        "center": [13.3250, 77.1000],
        "assigned_department": "Solid Waste Management Cell"
    }
]

def point_in_zone(lat, lng, bounds):
    """Checks if coordinates (lat, lng) lie within a rectangular geographical boundary."""
    if lat is None or lng is None:
        return False
    min_lat = min(bounds[0][0], bounds[1][0])
    max_lat = max(bounds[0][0], bounds[1][0])
    min_lng = min(bounds[0][1], bounds[1][1])
    max_lng = max(bounds[0][1], bounds[1][1])
    return (min_lat <= lat <= max_lat) and (min_lng <= lng <= max_lng)

def classify_zone_color(active_count):
    """
    Zone Classification Engine:
    - GREEN: 0 to 3 active complaints (#16A34A)
    - ORANGE: 4 to 7 active complaints (#F97316)
    - RED: 8 to 10 active complaints (#DC2626)
    - RED + WARNING: >10 active complaints (#DC2626)
    """
    if active_count <= 3:
        return {
            "tier": "GREEN",
            "color": "#16A34A",
            "meaning": "Low complaint area",
            "label": "Low Risk (Green Zone)",
            "warning": None
        }
    elif active_count <= 7:
        return {
            "tier": "ORANGE",
            "color": "#F97316",
            "meaning": "Medium complaint area",
            "label": "Moderate Alert (Orange Zone)",
            "warning": None
        }
    elif active_count <= 10:
        return {
            "tier": "RED",
            "color": "#DC2626",
            "meaning": "High complaint area",
            "label": "High Hazard Alert (Red Zone)",
            "warning": None
        }
    else:
        return {
            "tier": "RED",
            "color": "#DC2626",
            "meaning": "Critical civic congestion area",
            "label": "CRITICAL CONGESTION (Red Zone)",
            "warning": f"HIGH-VOLUME EMERGENCY WARNING: {active_count} active complaints require immediate zonal dispatch."
        }

@app.route("/api/zones", methods=["GET"])
@require_auth
def get_zones_summary(user):
    """
    Returns geographical zone classifications, active counts, and color codes.
    Excludes Resolved and Rejected complaints.
    """
    conn = get_connection()
    cursor = conn.cursor()

    # Active complaints
    cursor.execute("""
        SELECT r.id, r.report_id, r.tracking_id, r.title, r.complaint_title, r.category,
               r.department, r.priority, r.description, r.location, r.ward,
               r.latitude, r.longitude, r.image_filename, r.image_path, r.status,
               r.admin_remarks, r.created_at,
               a.detected_class, a.confidence_score
        FROM reports r
        LEFT JOIN ai_detections a ON r.report_id = a.report_id
        WHERE r.status IN ('Submitted', 'Under Review', 'In Progress', 'Dispatched')
          AND r.latitude IS NOT NULL AND r.longitude IS NOT NULL
        ORDER BY r.created_at DESC
    """)
    active_rows = [dict(row) for row in cursor.fetchall()]

    # Total resolved complaints
    cursor.execute("SELECT COUNT(*) FROM reports WHERE status = 'Resolved'")
    resolved_count = cursor.fetchone()[0]

    # Total rejected complaints
    cursor.execute("SELECT COUNT(*) FROM reports WHERE status = 'Rejected'")
    rejected_count = cursor.fetchone()[0]

    conn.close()

    # Distribute complaints into zones
    zone_results = []
    claimed_report_ids = set()

    for z in MUNICIPAL_ZONES:
        z_complaints = []
        for rep in active_rows:
            if rep["report_id"] not in claimed_report_ids:
                if point_in_zone(rep["latitude"], rep["longitude"], z["bounds"]):
                    z_complaints.append(rep)
                    claimed_report_ids.add(rep["report_id"])

        active_count = len(z_complaints)
        classification = classify_zone_color(active_count)

        zone_results.append({
            "zone_id": z["id"],
            "name": z["name"],
            "description": z["description"],
            "bounds": z["bounds"],
            "center": z["center"],
            "assigned_department": z["assigned_department"],
            "active_complaints": active_count,
            "tier": classification["tier"],
            "color": classification["color"],
            "meaning": classification["meaning"],
            "label": classification["label"],
            "warning": classification["warning"],
            "complaints": z_complaints
        })

    # Summary statistics
    green_count = sum(1 for z in zone_results if z["tier"] == "GREEN")
    orange_count = sum(1 for z in zone_results if z["tier"] == "ORANGE")
    red_count = sum(1 for z in zone_results if z["tier"] == "RED")

    return jsonify({
        "success": True,
        "total_zones": len(zone_results),
        "green_zones": green_count,
        "orange_zones": orange_count,
        "red_zones": red_count,
        "total_active_complaints": len(active_rows),
        "total_resolved_complaints": resolved_count,
        "total_rejected_complaints": rejected_count,
        "zones": zone_results,
        "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    })

@app.route("/api/zones/<zone_id>/complaints", methods=["GET"])
@require_auth
def get_zone_complaints(user, zone_id):
    """Fetches all active complaints located inside a specific geographical zone."""
    target_zone = next((z for z in MUNICIPAL_ZONES if z["id"].upper() == zone_id.upper()), None)
    if not target_zone:
        return jsonify({"error": f"Zone {zone_id} not recognized."}), 404

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT r.id, r.report_id, r.tracking_id, r.title, r.complaint_title, r.category,
               r.department, r.priority, r.description, r.location, r.ward,
               r.latitude, r.longitude, r.image_filename, r.image_path, r.status,
               r.admin_remarks, r.created_at,
               a.detected_class, a.confidence_score, a.model_name
        FROM reports r
        LEFT JOIN ai_detections a ON r.report_id = a.report_id
        WHERE r.status IN ('Submitted', 'Under Review', 'In Progress', 'Dispatched')
          AND r.latitude IS NOT NULL AND r.longitude IS NOT NULL
        ORDER BY r.created_at DESC
    """)
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()

    zone_complaints = [r for r in rows if point_in_zone(r["latitude"], r["longitude"], target_zone["bounds"])]
    classification = classify_zone_color(len(zone_complaints))

    return jsonify({
        "zone_id": target_zone["id"],
        "name": target_zone["name"],
        "description": target_zone["description"],
        "bounds": target_zone["bounds"],
        "center": target_zone["center"],
        "active_count": len(zone_complaints),
        "classification": classification,
        "complaints": zone_complaints
    })

# ==========================================================
# MODULE 3: AI DETECTION DASHBOARD & METRICS
# ==========================================================

@app.route("/api/ai/metrics", methods=["GET"])
@require_admin
def get_ai_metrics(user):
    """
    Module 3 Real AI Detection Metrics.
    Aggregates actual database records from ai_detections and reports.
    No hardcoded random or fake numbers.
    """
    conn = get_connection()
    cursor = conn.cursor()

    # Total AI analysed images
    cursor.execute("SELECT COUNT(*) FROM ai_detections")
    total_analyzed = cursor.fetchone()[0]

    # Detections by class
    cursor.execute("""
        SELECT detected_class, COUNT(*)
        FROM ai_detections
        WHERE detection_status = 'SUCCESS'
        GROUP BY detected_class
    """)
    class_counts = {row[0]: row[1] for row in cursor.fetchall()}

    # Detection failures / manual fallbacks
    cursor.execute("SELECT COUNT(*) FROM ai_detections WHERE detection_status != 'SUCCESS'")
    failures = cursor.fetchone()[0]

    # Average confidence score across successful detections
    cursor.execute("SELECT AVG(confidence_score) FROM ai_detections WHERE detection_status = 'SUCCESS'")
    avg_conf_row = cursor.fetchone()[0]
    avg_conf = round(float(avg_conf_row), 3) if avg_conf_row else 0.0

    # Recent AI detections log
    cursor.execute("""
        SELECT a.detection_id, a.report_id, a.detected_class, a.confidence_score,
               a.model_name, a.suggested_category, a.citizen_confirmed_category,
               a.detection_status, a.detected_at, r.title, r.status, r.priority, r.image_filename
        FROM ai_detections a
        JOIN reports r ON a.report_id = r.report_id
        ORDER BY a.detected_at DESC
        LIMIT 20
    """)
    recent_detections = [dict(r) for r in cursor.fetchall()]

    conn.close()

    return jsonify({
        "total_analyzed": total_analyzed,
        "total_supported_detections": sum(class_counts.values()),
        "potholes_detected": class_counts.get("Potholes", 0),
        "garbage_detected": class_counts.get("Garbage accumulation", 0),
        "road_damage_detected": class_counts.get("Road damage", 0),
        "drainage_detected": class_counts.get("Drainage problems", 0),
        "water_leakage_detected": class_counts.get("Water leakage", 0),
        "detection_failures": failures,
        "avg_confidence_score": avg_conf,
        "avg_confidence_percent": f"{int(avg_conf * 100)}%",
        "class_breakdown": class_counts,
        "recent_detections": recent_detections
    })

@app.route("/api/admin/metrics", methods=["GET"])
@require_admin
def get_metrics(user):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM reports")
    total = cursor.fetchone()[0]

    cursor.execute("SELECT status, COUNT(*) FROM reports GROUP BY status")
    by_status = {row[0]: row[1] for row in cursor.fetchall()}

    cursor.execute("SELECT category, COUNT(*) FROM reports GROUP BY category")
    by_category = {row[0]: row[1] for row in cursor.fetchall()}

    cursor.execute("SELECT priority, COUNT(*) FROM reports GROUP BY priority")
    by_priority = {row[0]: row[1] for row in cursor.fetchall()}

    cursor.execute("SELECT COUNT(*) FROM users WHERE role = 'citizen'")
    citizen_count = cursor.fetchone()[0]

    # AI count summary
    cursor.execute("SELECT COUNT(*) FROM ai_detections WHERE detection_status = 'SUCCESS'")
    ai_success = cursor.fetchone()[0]

    conn.close()

    return jsonify({
        "total": total,
        "citizens": citizen_count,
        "submitted": by_status.get("Submitted", 0),
        "underReview": by_status.get("Under Review", 0),
        "inProgress": by_status.get("In Progress", 0) + by_status.get("Dispatched", 0),
        "resolved": by_status.get("Resolved", 0),
        "rejected": by_status.get("Rejected", 0),
        "ai_detections_count": ai_success,
        "byCategory": by_category,
        "byPriority": by_priority
    })

# Serve uploaded evidence images safely and securely
@app.route("/api/uploads/<path:filename>")
def serve_upload(filename):
    clean_name = secure_filename(os.path.basename(filename))
    file_path = os.path.join(UPLOADS_DIR, clean_name)
    if not os.path.isfile(file_path):
        return jsonify({"error": "Evidence photograph not found on server."}), 404
    return send_from_directory(UPLOADS_DIR, clean_name)

# Serve Frontend SPA
@app.route("/")
def index():
    return send_from_directory(BASE_DIR, "index.html")

@app.route("/<path:path>")
def static_proxy(path):
    if os.path.exists(os.path.join(BASE_DIR, path)):
        return send_from_directory(BASE_DIR, path)
    return send_from_directory(BASE_DIR, "index.html")

if __name__ == "__main__":
    if sys.stdout and hasattr(sys.stdout, 'reconfigure'):
        try:
            sys.stdout.reconfigure(encoding='utf-8')
        except Exception:
            pass
    print("\n=======================================================")
    print("CITIZENSHIELD ROBUST MUNICIPAL BACKEND SERVER")
    print("=======================================================")
    print(f"* Persistent Database: {DB_PATH}")
    print(f"* Uploads Vault:       {UPLOADS_DIR}")
    print("* Server Listening on: http://127.0.0.1:5000")
    print("=======================================================\n")
    app.run(host="0.0.0.0", port=5000, debug=False)
