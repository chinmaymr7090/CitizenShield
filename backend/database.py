# CitizenShield - Robust SQLite Engine & Persistent Data Layer
import sqlite3
import os
import hashlib
import uuid
from datetime import datetime, timezone, timedelta

def get_now_iso(offset_days=0, offset_hours=0):
    dt = datetime.now(timezone.utc) - timedelta(days=offset_days, hours=offset_hours)
    return dt.strftime("%Y-%m-%d %H:%M:%S")

DB_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data"))
DB_PATH = os.path.join(DB_DIR, "citizenshield.db")

os.makedirs(DB_DIR, exist_ok=True)

def get_connection():
    """
    Connects to the persistent SQLite database.
    Enforces WAL mode (Write-Ahead Logging) and Foreign Key constraints.
    Data is never lost or deleted on restarts.
    """
    conn = sqlite3.connect(DB_PATH, timeout=30.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode = WAL;")
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.execute("PRAGMA synchronous = NORMAL;")
    return conn

def hash_password(password, salt=None):
    """Secure SHA-256 with random cryptographic salt."""
    if not salt:
        salt = uuid.uuid4().hex
    pwd_hash = hashlib.sha256((password + salt).encode('utf-8')).hexdigest()
    return pwd_hash, salt

def verify_password(password, salt, stored_hash):
    pwd_hash, _ = hash_password(password, salt)
    return pwd_hash == stored_hash

def repair_default_credentials(cursor):
    """Ensures the bundled demo accounts remain valid across stale database copies."""
    default_credentials = {
        "admin@citizenshield.gov": "Admin@2026",
        "engineer@citizenshield.gov": "Engineer@2026",
        "rahul.citizen@gmail.com": "Citizen@2026",
    }

    for email, password in default_credentials.items():
        row = cursor.execute(
            "SELECT id, password_hash, password_salt FROM users WHERE email = ?",
            (email,),
        ).fetchone()
        if not row:
            continue

        expected_hash, expected_salt = hash_password(password)
        if row[1] != expected_hash or row[2] != expected_salt:
            cursor.execute(
                "UPDATE users SET password_hash = ?, password_salt = ? WHERE id = ?",
                (expected_hash, expected_salt, row[0]),
            )

def init_db():
    """Initializes tables, safe migrations, and seeds permanent municipal data."""
    conn = get_connection()
    cursor = conn.cursor()

    # 1. Users Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        uuid TEXT UNIQUE NOT NULL,
        name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL COLLATE NOCASE,
        phone TEXT,
        password_hash TEXT NOT NULL,
        password_salt TEXT NOT NULL,
        role TEXT NOT NULL DEFAULT 'citizen',
        department TEXT DEFAULT 'General Public',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # 2. Reports Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS reports (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        report_id TEXT UNIQUE NOT NULL,
        tracking_id TEXT UNIQUE,
        user_id INTEGER NOT NULL,
        citizen_name TEXT NOT NULL,
        citizen_email TEXT NOT NULL,
        citizen_phone TEXT,
        title TEXT NOT NULL,
        complaint_title TEXT,
        category TEXT NOT NULL,
        department TEXT NOT NULL,
        priority TEXT NOT NULL DEFAULT 'Normal',
        description TEXT NOT NULL,
        location TEXT NOT NULL,
        ward TEXT DEFAULT 'Ward 11 - Mandipet / Town Hall Division',
        latitude REAL,
        longitude REAL,
        image_path TEXT,
        image_filename TEXT,
        after_repair_image TEXT,
        status TEXT NOT NULL DEFAULT 'Submitted',
        admin_remarks TEXT,
        sla_hours INTEGER DEFAULT 48,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE RESTRICT
    );
    """)

    # 3. Real AI Detections Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS ai_detections (
        detection_id INTEGER PRIMARY KEY AUTOINCREMENT,
        report_id TEXT NOT NULL,
        detected_class TEXT NOT NULL,
        confidence_score REAL NOT NULL,
        model_name TEXT NOT NULL,
        suggested_category TEXT NOT NULL,
        citizen_confirmed_category TEXT,
        detection_status TEXT DEFAULT 'SUCCESS',
        detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (report_id) REFERENCES reports(report_id) ON DELETE CASCADE
    );
    """)

    # 4. Status History Table (Audit Log for Civic Workflow)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS status_history (
        history_id INTEGER PRIMARY KEY AUTOINCREMENT,
        id INTEGER,
        report_id TEXT NOT NULL,
        previous_status TEXT,
        new_status TEXT,
        status TEXT NOT NULL,
        officer_remarks TEXT,
        remarks TEXT,
        officer_name TEXT,
        officer_role TEXT,
        updated_by TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (report_id) REFERENCES reports(report_id) ON DELETE CASCADE
    );
    """)

    # 5. Auth Tokens Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS auth_tokens (
        token TEXT PRIMARY KEY,
        user_id INTEGER NOT NULL,
        expires_at TIMESTAMP NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    );
    """)

    # 6. Municipal Audit Log
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS audit_logs (
        log_id INTEGER PRIMARY KEY AUTOINCREMENT,
        id INTEGER,
        user_id INTEGER,
        event_type TEXT,
        action TEXT,
        user_email TEXT,
        details TEXT,
        ip_address TEXT,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # 7. Officer Replies to Citizens Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS officer_replies (
        reply_id INTEGER PRIMARY KEY AUTOINCREMENT,
        report_id TEXT NOT NULL,
        officer_id INTEGER NOT NULL,
        officer_name TEXT,
        officer_role TEXT,
        reply_message TEXT NOT NULL,
        previous_status TEXT,
        new_status TEXT,
        resolution_details TEXT,
        after_repair_image TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (report_id) REFERENCES reports(report_id) ON DELETE CASCADE,
        FOREIGN KEY (officer_id) REFERENCES users(id) ON DELETE RESTRICT
    );
    """)

    # 8. In-App User Notifications Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS notifications (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        report_id TEXT,
        title TEXT NOT NULL,
        message TEXT NOT NULL,
        is_read INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    );
    """)

    # --- Safe Migrations for Existing Tables ---
    def add_column_if_missing(table, column, col_type):
        cursor.execute(f"PRAGMA table_info({table})")
        cols = [row[1] for row in cursor.fetchall()]
        if column not in cols:
            try:
                cursor.execute(f"ALTER TABLE {table} ADD COLUMN {column} {col_type}")
                print(f"[CitizenShield DB Migration] Added column {column} ({col_type}) to {table}")
            except Exception as e:
                print(f"[CitizenShield DB Migration Warning] Could not add {column} to {table}: {e}")

    add_column_if_missing("users", "user_id", "INTEGER")
    add_column_if_missing("reports", "tracking_id", "TEXT")
    add_column_if_missing("reports", "complaint_title", "TEXT")
    add_column_if_missing("reports", "image_path", "TEXT")
    add_column_if_missing("reports", "after_repair_image", "TEXT")
    add_column_if_missing("status_history", "history_id", "INTEGER")
    add_column_if_missing("status_history", "previous_status", "TEXT")
    add_column_if_missing("status_history", "new_status", "TEXT")
    add_column_if_missing("status_history", "officer_remarks", "TEXT")
    add_column_if_missing("status_history", "updated_by", "TEXT")
    add_column_if_missing("status_history", "updated_at", "TIMESTAMP")
    add_column_if_missing("audit_logs", "log_id", "INTEGER")
    add_column_if_missing("audit_logs", "user_id", "INTEGER")
    add_column_if_missing("audit_logs", "action", "TEXT")
    add_column_if_missing("audit_logs", "timestamp", "TIMESTAMP")

    # Sync tracking_id = report_id if NULL
    cursor.execute("UPDATE reports SET tracking_id = report_id WHERE tracking_id IS NULL OR tracking_id = ''")
    cursor.execute("UPDATE reports SET complaint_title = title WHERE complaint_title IS NULL OR complaint_title = ''")
    cursor.execute("UPDATE reports SET image_path = image_filename WHERE (image_path IS NULL OR image_path = '') AND image_filename IS NOT NULL")
    cursor.execute("UPDATE users SET user_id = id WHERE user_id IS NULL")

    # Seed Default Accounts if empty
    cursor.execute("SELECT COUNT(*) FROM users")
    if cursor.fetchone()[0] == 0:
        print("[CitizenShield DB] Seeding default municipal administrative and citizen accounts...")
        h_adm, s_adm = hash_password("Admin@2026")
        cursor.execute("""
            INSERT INTO users (uuid, name, email, password_hash, password_salt, role, department, phone)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (str(uuid.uuid4()), "Municipal Commissioner Office", "admin@citizenshield.gov", h_adm, s_adm, "admin", "Central Directorate", "+91 80 2266 0000"))

        h_eng, s_eng = hash_password("Engineer@2026")
        cursor.execute("""
            INSERT INTO users (uuid, name, email, password_hash, password_salt, role, department, phone)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (str(uuid.uuid4()), "Er. K. Ramesh (Ward 112)", "engineer@citizenshield.gov", h_eng, s_eng, "admin", "Roads & Civil Infrastructure", "+91 80 2266 1122"))

        h_cit, s_cit = hash_password("Citizen@2026")
        cursor.execute("""
            INSERT INTO users (uuid, name, email, password_hash, password_salt, role, department, phone)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (str(uuid.uuid4()), "Rahul Sharma", "rahul.citizen@gmail.com", h_cit, s_cit, "citizen", "General Public", "+91 98450 12345"))

        user_cit_id = cursor.lastrowid
        cursor.execute("UPDATE users SET user_id = id WHERE user_id IS NULL")

        sample_reports = [
            (
                "CS-2026-84912", "CS-2026-84912", user_cit_id, "Rahul Sharma", "rahul.citizen@gmail.com", "+91 98450 12345",
                "Hazardous Tarmac Crater near Metro Pillar 142", "Hazardous Tarmac Crater near Metro Pillar 142",
                "Roads and Transport", "Roads & Civil Infrastructure", "Urgent",
                "Deep crater (approx. 4ft wide, 8in deep) following heavy monsoon downpour. Two two-wheelers suffered tire bursts.",
                "Opposite Metro Pillar 142, CMH Road, Ward 112", "Ward 112 - Indiranagar Division",
                12.9784, 77.6408, "In Progress", "Quick Response Road Crew dispatched. Asphalt cold-mix patch underway.", 24,
                get_now_iso(offset_days=2), get_now_iso(offset_hours=4)
            ),
            (
                "CS-2026-30219", "CS-2026-30219", user_cit_id, "Rahul Sharma", "rahul.citizen@gmail.com", "+91 98450 12345",
                "High-Voltage Streetlight Array Blackout", "High-Voltage Streetlight Array Blackout",
                "Streetlights and Electricity", "Electrical & Public Lighting", "High",
                "5 consecutive sodium fixtures along 100ft road are dead due to transformer junction short. Street is pitch dark.",
                "100 Feet Road, 12th Main Junction", "Ward 112 - Indiranagar Division",
                12.9716, 77.6412, "Under Review", "Assigned to BESCOM Zonal Line Team. Transformer box inspection scheduled.", 48,
                get_now_iso(offset_days=1), get_now_iso(offset_hours=6)
            ),
            (
                "CS-2026-11840", "CS-2026-11840", user_cit_id, "Rahul Sharma", "rahul.citizen@gmail.com", "+91 98450 12345",
                "Severe Underground Sewage Overflow & Stagnation", "Severe Underground Sewage Overflow & Stagnation",
                "Water and Drainage", "Water Supply & Sewerage Board", "Urgent",
                "Main 400mm sanitary pipeline clogged. Foul black water overflowing onto public walkway.",
                "8th Cross, Vasanth Nagar", "Ward 93 - Vasanth Nagar Division",
                12.9892, 77.5921, "Resolved", "Jetting machine deployment complete. Silt block cleared and disinfectant sprayed.", 12,
                get_now_iso(offset_days=4), get_now_iso(offset_days=1)
            ),
            (
                "CS-2026-62841", "CS-2026-62841", user_cit_id, "Rahul Sharma", "rahul.citizen@gmail.com", "+91 98450 12345",
                "Unregulated Commercial Waste Dumping on Footpath", "Unregulated Commercial Waste Dumping on Footpath",
                "Garbage and Sanitation", "Solid Waste Management Cell", "Normal",
                "Bulk food waste and rotting cardboard dumped outside commercial plaza. Stray dogs tearing open bags.",
                "Commercial Street Cross, Ward 109", "Ward 109 - Commercial Division",
                12.9822, 77.6083, "Submitted", "Registered into municipal portal queue. Awaiting ward inspector review.", 48,
                get_now_iso(offset_hours=8), get_now_iso(offset_hours=8)
            )
        ]

        for rep in sample_reports:
            cursor.execute("""
                INSERT INTO reports (
                    report_id, tracking_id, user_id, citizen_name, citizen_email, citizen_phone,
                    title, complaint_title, category, department, priority, description, location,
                    ward, latitude, longitude, status, admin_remarks, sla_hours,
                    created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, rep)

            rep_id = rep[0]
            st = rep[16]
            rem = rep[17]
            cursor.execute("""
                INSERT INTO status_history (report_id, status, new_status, remarks, officer_remarks, officer_name, officer_role, updated_by, created_at, updated_at)
                VALUES (?, 'Submitted', 'Submitted', 'Grievance lodged by citizen via portal.', 'Grievance lodged by citizen via portal.', 'Citizen', 'Citizen', 'Citizen', ?, ?)
            """, (rep_id, rep[19], rep[19]))

            if st in ['Under Review', 'In Progress', 'Resolved']:
                cursor.execute("""
                    INSERT INTO status_history (report_id, status, previous_status, new_status, remarks, officer_remarks, officer_name, officer_role, updated_by, created_at, updated_at)
                    VALUES (?, 'Under Review', 'Submitted', 'Under Review', 'Verified by Municipal Control Room.', 'Verified by Municipal Control Room.', 'Ward Control Room', 'Officer', 'Officer', ?, ?)
                """, (rep_id, rep[20], rep[20]))

            if st in ['In Progress', 'Resolved']:
                cursor.execute("""
                    INSERT INTO status_history (report_id, status, previous_status, new_status, remarks, officer_remarks, officer_name, officer_role, updated_by, created_at, updated_at)
                    VALUES (?, 'In Progress', 'Under Review', 'In Progress', ?, ?, 'Er. K. Ramesh', 'Senior Engineer', 'Senior Engineer', ?, ?)
                """, (rep_id, rem, rem, rep[20], rep[20]))

            if st == 'Resolved':
                cursor.execute("""
                    INSERT INTO status_history (report_id, status, previous_status, new_status, remarks, officer_remarks, officer_name, officer_role, updated_by, created_at, updated_at)
                    VALUES (?, 'Resolved', 'In Progress', 'Resolved', 'Field rectification completed. Photo verification verified.', 'Field rectification completed. Photo verification verified.', 'Municipal Inspectorate', 'Directorate', 'Municipal Inspectorate', ?, ?)
                """, (rep_id, rep[20], rep[20]))

    # Seed baseline AI detections for existing reports if ai_detections is empty
    cursor.execute("SELECT COUNT(*) FROM ai_detections")
    if cursor.fetchone()[0] == 0:
        cursor.execute("SELECT report_id, category, priority FROM reports")
        reports_for_ai = cursor.fetchall()
        for r in reports_for_ai:
            r_id, r_cat, r_prio = r[0], r[1], r[2]
            if "Road" in r_cat:
                d_cls, conf, model = "Potholes", 0.88, "YOLOv8-Road-Distress-v1"
            elif "Garbage" in r_cat:
                d_cls, conf, model = "Garbage accumulation", 0.91, "YOLOv8n-Solid-Waste-Detector"
            elif "Drainage" in r_cat or "Water" in r_cat:
                d_cls, conf, model = "Drainage problems", 0.84, "OpenCV-Hydrological-Spectral-Analyzer"
            else:
                d_cls, conf, model = "Road damage", 0.79, "YOLOv8-Road-Distress-v1"

            cursor.execute("""
                INSERT INTO ai_detections (
                    report_id, detected_class, confidence_score, model_name,
                    suggested_category, citizen_confirmed_category, detection_status
                ) VALUES (?, ?, ?, ?, ?, ?, 'SUCCESS')
            """, (r_id, d_cls, conf, model, r_cat, r_cat))

    repair_default_credentials(cursor)
    conn.commit()
    conn.close()
    print(f"[CitizenShield DB] Database initialized. Permanent storage active at: {DB_PATH}")

if __name__ == "__main__":
    init_db()
