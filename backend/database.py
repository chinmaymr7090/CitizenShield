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
    """Initializes tables and seeds permanent default administrative and citizen data."""
    conn = get_connection()
    cursor = conn.cursor()

    # 1. Users Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        uuid TEXT UNIQUE NOT NULL,
        name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL COLLATE NOCASE,
        password_hash TEXT NOT NULL,
        password_salt TEXT NOT NULL,
        role TEXT NOT NULL DEFAULT 'citizen',
        department TEXT DEFAULT 'General Public',
        phone TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # 2. Reports Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS reports (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        report_id TEXT UNIQUE NOT NULL,
        user_id INTEGER NOT NULL,
        citizen_name TEXT NOT NULL,
        citizen_email TEXT NOT NULL,
        citizen_phone TEXT,
        title TEXT NOT NULL,
        category TEXT NOT NULL,
        department TEXT NOT NULL,
        priority TEXT NOT NULL DEFAULT 'Normal',
        description TEXT NOT NULL,
        location TEXT NOT NULL,
        ward TEXT DEFAULT 'Ward 112 - Central Division',
        latitude REAL,
        longitude REAL,
        image_filename TEXT,
        status TEXT NOT NULL DEFAULT 'Submitted',
        admin_remarks TEXT,
        sla_hours INTEGER DEFAULT 48,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE RESTRICT
    );
    """)

    # 3. Status History Table (Audit Log for Civic Workflow)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS status_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        report_id TEXT NOT NULL,
        status TEXT NOT NULL,
        remarks TEXT,
        officer_name TEXT,
        officer_role TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (report_id) REFERENCES reports(report_id) ON DELETE CASCADE
    );
    """)

    # 4. Auth Tokens Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS auth_tokens (
        token TEXT PRIMARY KEY,
        user_id INTEGER NOT NULL,
        expires_at TIMESTAMP NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    );
    """)

    # 5. Municipal Audit Log
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS audit_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        event_type TEXT NOT NULL,
        user_email TEXT,
        details TEXT,
        ip_address TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # Seed Default Accounts if empty, and repair stale bundled credentials on older DB snapshots.
    cursor.execute("SELECT COUNT(*) FROM users")
    if cursor.fetchone()[0] == 0:
        print("[CitizenShield DB] Seeding default municipal administrative and citizen accounts...")
        
        # 1. Super Admin Officer
        h_adm, s_adm = hash_password("Admin@2026")
        cursor.execute("""
            INSERT INTO users (uuid, name, email, password_hash, password_salt, role, department, phone)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (str(uuid.uuid4()), "Municipal Commissioner Office", "admin@citizenshield.gov", h_adm, s_adm, "admin", "Central Directorate", "+91 80 2266 0000"))

        # 2. Ward Senior Engineer
        h_eng, s_eng = hash_password("Engineer@2026")
        cursor.execute("""
            INSERT INTO users (uuid, name, email, password_hash, password_salt, role, department, phone)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (str(uuid.uuid4()), "Er. K. Ramesh (Ward 112)", "engineer@citizenshield.gov", h_eng, s_eng, "admin", "Roads & Civil Infrastructure", "+91 80 2266 1122"))

        # 3. Registered Citizen
        h_cit, s_cit = hash_password("Citizen@2026")
        cursor.execute("""
            INSERT INTO users (uuid, name, email, password_hash, password_salt, role, department, phone)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (str(uuid.uuid4()), "Rahul Sharma", "rahul.citizen@gmail.com", h_cit, s_cit, "citizen", "General Public", "+91 98450 12345"))

        user_cit_id = cursor.lastrowid

        # Seed realistic civic complaints across central municipal wards
        sample_reports = [
            (
                "CS-2026-84912",
                user_cit_id,
                "Rahul Sharma",
                "rahul.citizen@gmail.com",
                "+91 98450 12345",
                "Hazardous Tarmac Crater near Metro Pillar 142",
                "Roads and Transport",
                "Roads & Civil Infrastructure",
                "Urgent",
                "Deep crater (approx. 4ft wide, 8in deep) following heavy monsoon downpour. Two two-wheelers suffered tire bursts. Immediate barricading and patch-fill required.",
                "Opposite Metro Pillar 142, CMH Road, Ward 112",
                "Ward 112 - Indiranagar Division",
                12.9784,
                77.6408,
                "In Progress",
                "Quick Response Road Crew dispatched. Asphalt cold-mix patch underway. Barricades erected for night safety.",
                24,
                get_now_iso(offset_days=2),
                get_now_iso(offset_hours=4)
            ),
            (
                "CS-2026-30219",
                user_cit_id,
                "Rahul Sharma",
                "rahul.citizen@gmail.com",
                "+91 98450 12345",
                "High-Voltage Streetlight Array Blackout",
                "Streetlights and Electricity",
                "Electrical & Public Lighting",
                "High",
                "5 consecutive sodium fixtures along 100ft road are dead due to transformer junction short. Street is pitch dark, creating serious safety risks for women and commuters.",
                "100 Feet Road, 12th Main Junction",
                "Ward 112 - Indiranagar Division",
                12.9716,
                77.6412,
                "Under Review",
                "Assigned to BESCOM Zonal Line Team. Transformer box inspection scheduled for 18:00 hrs.",
                48,
                get_now_iso(offset_days=1),
                get_now_iso(offset_hours=6)
            ),
            (
                "CS-2026-11840",
                user_cit_id,
                "Rahul Sharma",
                "rahul.citizen@gmail.com",
                "+91 98450 12345",
                "Severe Underground Sewage Overflow & Stagnation",
                "Water and Drainage",
                "Water Supply & Sewerage Board",
                "Urgent",
                "Main 400mm sanitary pipeline clogged. Foul black water overflowing onto public walkway and reaching apartment parking stilt.",
                "8th Cross, Vasanth Nagar",
                "Ward 93 - Vasanth Nagar Division",
                12.9892,
                77.5921,
                "Resolved",
                "Jetting machine deployment complete. Silt block cleared and disinfectant sprayed across road surface.",
                12,
                get_now_iso(offset_days=4),
                get_now_iso(offset_days=1)
            ),
            (
                "CS-2026-62841",
                user_cit_id,
                "Rahul Sharma",
                "rahul.citizen@gmail.com",
                "+91 98450 12345",
                "Unregulated Commercial Waste Dumping on Footpath",
                "Garbage and Sanitation",
                "Solid Waste Management Cell",
                "Normal",
                "Bulk food waste and rotting cardboard dumped outside commercial plaza. Stray dogs tearing open bags.",
                "Commercial Street Cross, Ward 109",
                "Ward 109 - Commercial Division",
                12.9822,
                77.6083,
                "Submitted",
                "Registered into municipal portal queue. Awaiting ward inspector review.",
                48,
                get_now_iso(offset_hours=8),
                get_now_iso(offset_hours=8)
            )
        ]

        for rep in sample_reports:
            cursor.execute("""
                INSERT INTO reports (
                    report_id, user_id, citizen_name, citizen_email, citizen_phone,
                    title, category, department, priority, description, location,
                    ward, latitude, longitude, status, admin_remarks, sla_hours,
                    created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, rep)

            # Insert history entries
            rep_id = rep[0]
            st = rep[14]
            rem = rep[15]
            cursor.execute("""
                INSERT INTO status_history (report_id, status, remarks, officer_name, officer_role, created_at)
                VALUES (?, 'Submitted', 'Grievance lodged by citizen via portal.', 'Citizen', 'Citizen', ?)
            """, (rep_id, rep[17]))

            if st in ['Under Review', 'In Progress', 'Resolved']:
                cursor.execute("""
                    INSERT INTO status_history (report_id, status, remarks, officer_name, officer_role, created_at)
                    VALUES (?, 'Under Review', 'Verified by Municipal Control Room. Work-ticket dispatched to zonal unit.', 'Ward Control Room', 'Officer', ?)
                """, (rep_id, rep[18]))

            if st in ['In Progress', 'Resolved']:
                cursor.execute("""
                    INSERT INTO status_history (report_id, status, remarks, officer_name, officer_role, created_at)
                    VALUES (?, 'In Progress', ?, 'Er. K. Ramesh', 'Senior Engineer', ?)
                """, (rep_id, rem, rep[18]))

            if st == 'Resolved':
                cursor.execute("""
                    INSERT INTO status_history (report_id, status, remarks, officer_name, officer_role, created_at)
                    VALUES (?, 'Resolved', 'Field rectification completed. Photo verification verified.', 'Municipal Inspectorate', 'Directorate', ?)
                """, (rep_id, rep[18]))

    repair_default_credentials(cursor)
    conn.commit()
    conn.close()
    print(f"[CitizenShield DB] Database initialized. Permanent storage active at: {DB_PATH}")

if __name__ == "__main__":
    init_db()
