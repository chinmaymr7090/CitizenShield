# CitizenShield - Robust Municipal Backend Server
import os
import uuid
import secrets
from datetime import datetime, timezone, timedelta
from functools import wraps
from flask import Flask, request, jsonify, send_from_directory, render_template
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

# App Configuration
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
UPLOADS_DIR = os.path.join(BASE_DIR, "uploads")
STATIC_DIR = os.path.join(BASE_DIR, "static")

os.makedirs(UPLOADS_DIR, exist_ok=True)
os.makedirs(STATIC_DIR, exist_ok=True)

app = Flask(__name__, static_folder=STATIC_DIR, static_url_path="/static")
CORS(app)
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024  # 10 MB Max upload
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp', 'gif'}

# Initialize database on startup
init_db()

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_current_user():
    """Extracts and verifies Bearer token from request."""
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        return None
    token = auth_header.split(" ", 1)[1].strip()
    if not token:
        return None

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT u.id, u.uuid, u.name, u.email, u.role, u.department, u.phone
        FROM auth_tokens t
        JOIN users u ON t.user_id = u.id
        WHERE t.token = ? AND t.expires_at > CURRENT_TIMESTAMP
    """, (token,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return dict(row)
    return None

def require_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        user = get_current_user()
        if not user:
            return jsonify({"error": "Unauthorized: Valid authentication token required"}), 401
        return f(user, *args, **kwargs)
    return decorated

def require_admin(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        user = get_current_user()
        if not user:
            return jsonify({"error": "Unauthorized: Authentication required"}), 401
        if user.get("role") not in ["admin", "officer"]:
            return jsonify({"error": "Forbidden: Municipal officer privileges required"}), 403
        return f(user, *args, **kwargs)
    return decorated

def log_audit(event_type, details, user_email="Anonymous"):
    """Appends an immutable security and action record."""
    try:
        ip = request.remote_addr or "127.0.0.1"
        conn = get_connection()
        conn.execute("""
            INSERT INTO audit_logs (event_type, user_email, details, ip_address)
            VALUES (?, ?, ?, ?)
        """, (event_type, user_email, details, ip))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"[Audit Log Error] {e}")

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

    if not name or not email or not password:
        return jsonify({"error": "Full Name, Email, and Password are required."}), 400

    if len(password) < 6:
        return jsonify({"error": "Password must be at least 6 characters long."}), 400

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT id FROM users WHERE email = ?", (email,))
    if cursor.fetchone():
        conn.close()
        return jsonify({"error": "An account with this email address already exists."}), 409

    pwd_hash, salt = hash_password(password)
    user_uuid = str(uuid.uuid4())
    role = "admin" if email.endswith("@citizenshield.gov") else "citizen"
    department = "Central Directorate" if role == "admin" else "General Public"

    cursor.execute("""
        INSERT INTO users (uuid, name, email, password_hash, password_salt, role, department, phone)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (user_uuid, name, email, pwd_hash, salt, role, department, phone))
    user_id = cursor.lastrowid

    # Create persistent session token
    token = secrets.token_hex(32)
    expires = (datetime.now(timezone.utc) + timedelta(days=30)).strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute("""
        INSERT INTO auth_tokens (token, user_id, expires_at)
        VALUES (?, ?, ?)
    """, (token, user_id, expires))

    conn.commit()
    conn.close()

    log_audit("USER_REGISTERED", f"Citizen registered: {email} ({name})", email)

    return jsonify({
        "message": "Registration successful",
        "token": token,
        "user": {
            "uuid": user_uuid,
            "name": name,
            "email": email,
            "role": role,
            "department": department,
            "phone": phone
        }
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
        SELECT id, uuid, name, email, password_hash, password_salt, role, department, phone
        FROM users WHERE email = ?
    """, (email,))
    user = cursor.fetchone()

    if not user or not verify_password(password, user["password_salt"], user["password_hash"]):
        conn.close()
        log_audit("LOGIN_FAILED", f"Invalid credentials attempt for: {email}", email)
        return jsonify({"error": "Invalid email or password. Please verify credentials."}), 401

    token = secrets.token_hex(32)
    expires = (datetime.now(timezone.utc) + timedelta(days=30)).strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute("""
        INSERT INTO auth_tokens (token, user_id, expires_at)
        VALUES (?, ?, ?)
    """, (token, user["id"], expires))

    conn.commit()
    conn.close()

    log_audit("LOGIN_SUCCESS", f"User logged in: {email} ({user['role']})", email)

    return jsonify({
        "message": "Authentication successful",
        "token": token,
        "user": {
            "uuid": user["uuid"],
            "name": user["name"],
            "email": user["email"],
            "role": user["role"],
            "department": user["department"],
            "phone": user["phone"]
        }
    }), 200

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
# REPORT MANAGEMENT ENDPOINTS
# ==========================================================

@app.route("/api/reports", methods=["POST"])
@require_auth
def create_report(user):
    # Form data or JSON
    if request.content_type and "multipart/form-data" in request.content_type:
        form = request.form
        files = request.files
    else:
        form = request.get_json(silent=True) or {}
        files = {}

    title = (form.get("title") or "").strip()
    category = (form.get("category") or "").strip()
    department = (form.get("department") or "Roads & Civil Infrastructure").strip()
    priority = (form.get("priority") or "Normal").strip()
    description = (form.get("description") or "").strip()
    location = (form.get("location") or "").strip()
    ward = (form.get("ward") or "Ward 112 - Central Division").strip()

    lat = form.get("latitude")
    lng = form.get("longitude")
    latitude = float(lat) if lat and str(lat).strip() else None
    longitude = float(lng) if lng and str(lng).strip() else None

    if not title or not category or not description or not location:
        return jsonify({"error": "Title, Category, Description, and Location are mandatory."}), 400

    # Handle image upload
    image_filename = None
    if "image" in files:
        file = files["image"]
        if file and file.filename and allowed_file(file.filename):
            ext = file.filename.rsplit('.', 1)[1].lower()
            unique_name = f"{int(datetime.now().timestamp())}_{uuid.uuid4().hex[:8]}.{ext}"
            file.save(os.path.join(UPLOADS_DIR, unique_name))
            image_filename = unique_name

    # SLA resolution target
    sla_map = {"Urgent": 12, "High": 24, "Normal": 48, "Low": 72}
    sla_hours = sla_map.get(priority, 48)

    # Human-readable Report ID (e.g. CS-2026-78491)
    year = datetime.now().year
    random_num = secrets.randbelow(90000) + 10000
    report_id = f"CS-{year}-{random_num}"

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO reports (
            report_id, user_id, citizen_name, citizen_email, citizen_phone,
            title, category, department, priority, description, location,
            ward, latitude, longitude, image_filename, status, admin_remarks,
            sla_hours
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'Submitted', '', ?)
    """, (
        report_id, user["id"], user["name"], user["email"], user.get("phone", ""),
        title, category, department, priority, description, location,
        ward, latitude, longitude, image_filename, sla_hours
    ))

    # Add initial status history entry
    cursor.execute("""
        INSERT INTO status_history (report_id, status, remarks, officer_name, officer_role)
        VALUES (?, 'Submitted', 'Official grievance lodged via citizen portal.', 'Citizen Submitter', 'Citizen')
    """, (report_id,))

    conn.commit()
    conn.close()

    log_audit("REPORT_CREATED", f"Grievance {report_id} registered: {title} ({category})", user["email"])

    return jsonify({
        "message": "Grievance successfully recorded in municipal registry.",
        "report_id": report_id,
        "status": "Submitted"
    }), 201

@app.route("/api/reports/my", methods=["GET"])
@require_auth
def get_my_reports(user):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM reports WHERE user_id = ? ORDER BY created_at DESC
    """, (user["id"],))
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return jsonify({"reports": rows})

@app.route("/api/reports/track/<report_id>", methods=["GET"])
def track_report(report_id):
    clean_id = (report_id or "").strip().upper()
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM reports WHERE report_id = ?", (clean_id,))
    report = cursor.fetchone()
    if not report:
        conn.close()
        return jsonify({"error": f"No municipal record found for Report ID: {clean_id}"}), 404

    report_dict = dict(report)

    # Fetch status history
    cursor.execute("""
        SELECT status, remarks, officer_name, officer_role, created_at
        FROM status_history
        WHERE report_id = ?
        ORDER BY created_at ASC
    """, (clean_id,))
    history = [dict(h) for h in cursor.fetchall()]
    report_dict["status_history"] = history

    conn.close()
    return jsonify({"report": report_dict})

@app.route("/api/reports/all", methods=["GET"])
@require_admin
def get_all_reports(user):
    status = request.args.get("status")
    category = request.args.get("category")
    priority = request.args.get("priority")
    search = request.args.get("search", "").strip()

    query = "SELECT * FROM reports WHERE 1=1"
    params = []

    if status and status != "ALL":
        query += " AND status = ?"
        params.append(status)

    if category and category != "ALL":
        query += " AND category = ?"
        params.append(category)

    if priority and priority != "ALL":
        query += " AND priority = ?"
        params.append(priority)

    if search:
        query += " AND (report_id LIKE ? OR title LIKE ? OR citizen_name LIKE ? OR location LIKE ?)"
        like_term = f"%{search}%"
        params.extend([like_term, like_term, like_term, like_term])

    query += " ORDER BY created_at DESC"

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
        SELECT report_id, title, category, department, priority, status,
               location, ward, latitude, longitude, created_at
        FROM reports
        WHERE latitude IS NOT NULL AND longitude IS NOT NULL
        ORDER BY created_at DESC
    """)
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return jsonify({"pins": rows})

@app.route("/api/reports/<report_id>/status", methods=["PATCH"])
@require_admin
def update_report_status(user, report_id):
    clean_id = (report_id or "").strip().upper()
    data = request.get_json(silent=True) or {}
    new_status = data.get("status")
    remarks = (data.get("remarks") or "").strip()
    department = data.get("department")

    valid_statuses = ["Submitted", "Under Review", "Dispatched", "In Progress", "Resolved", "Rejected"]
    if not new_status or new_status not in valid_statuses:
        return jsonify({"error": f"Invalid status. Must be one of: {', '.join(valid_statuses)}"}), 400

    if not remarks:
        return jsonify({"error": "Administrative justification and action remarks are required."}), 400

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT id, status, title FROM reports WHERE report_id = ?", (clean_id,))
    report = cursor.fetchone()
    if not report:
        conn.close()
        return jsonify({"error": "Report not found."}), 404

    now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")

    if department:
        cursor.execute("""
            UPDATE reports
            SET status = ?, admin_remarks = ?, department = ?, updated_at = ?
            WHERE report_id = ?
        """, (new_status, remarks, department, now_str, clean_id))
    else:
        cursor.execute("""
            UPDATE reports
            SET status = ?, admin_remarks = ?, updated_at = ?
            WHERE report_id = ?
        """, (new_status, remarks, now_str, clean_id))

    # Append to status history
    cursor.execute("""
        INSERT INTO status_history (report_id, status, remarks, officer_name, officer_role, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (clean_id, new_status, remarks, user["name"], user.get("role", "Officer").title(), now_str))

    conn.commit()
    conn.close()

    log_audit("STATUS_UPDATED", f"{clean_id} changed to {new_status} by {user['name']}: {remarks}", user["email"])

    return jsonify({
        "message": f"Report {clean_id} updated to {new_status}.",
        "report_id": clean_id,
        "status": new_status,
        "remarks": remarks
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

    conn.close()

    return jsonify({
        "total": total,
        "citizens": citizen_count,
        "submitted": by_status.get("Submitted", 0),
        "underReview": by_status.get("Under Review", 0),
        "inProgress": by_status.get("In Progress", 0) + by_status.get("Dispatched", 0),
        "resolved": by_status.get("Resolved", 0),
        "rejected": by_status.get("Rejected", 0),
        "byCategory": by_category,
        "byPriority": by_priority
    })

# Reverse Geocoding Proxy to bypass mobile browser CORS & HTTP mixed-content blocks
@app.route("/api/reverse-geocode")
def reverse_geocode():
    lat = request.args.get("lat")
    lon = request.args.get("lon")
    if not lat or not lon:
        return jsonify({"error": "Latitude and longitude required"}), 400
    try:
        import urllib.request
        import json
        url = f"https://nominatim.openstreetmap.org/reverse?format=jsonv2&lat={lat}&lon={lon}"
        req = urllib.request.Request(url, headers={"User-Agent": "CitizenShield-MunicipalPortal/1.0"})
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return jsonify({
                "display_name": data.get("display_name", ""),
                "address": data.get("address", {})
            })
    except Exception as e:
        return jsonify({"error": str(e), "display_name": f"Lat {lat}, Lng {lon}"}), 200

# IP-based Geolocation Fallback when device GPS is disabled or blocked
@app.route("/api/ip-location")
def ip_location():
    try:
        import urllib.request
        import json
        req = urllib.request.Request("https://ipapi.co/json/", headers={"User-Agent": "CitizenShield-MunicipalPortal/1.0"})
        with urllib.request.urlopen(req, timeout=4) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return jsonify({
                "latitude": data.get("latitude", 12.9716),
                "longitude": data.get("longitude", 77.5946),
                "city": data.get("city", "Bengaluru"),
                "region": data.get("region", "Karnataka")
            })
    except Exception:
        # Fallback to central Bengaluru default
        return jsonify({
            "latitude": 12.9716,
            "longitude": 77.5946,
            "city": "Bengaluru",
            "region": "Karnataka"
        })

# Serve uploaded evidence images safely
@app.route("/api/uploads/<path:filename>")
def serve_upload(filename):
    return send_from_directory(UPLOADS_DIR, secure_filename(filename))

# Serve Frontend SPA
@app.route("/")
def index():
    return send_from_directory(BASE_DIR, "index.html")

@app.route("/<path:path>")
def static_proxy(path):
    # Try serving from root or static
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
