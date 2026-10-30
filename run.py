# CitizenShield - Robust Production WSGI Server Launcher
import os
import sys

# Ensure UTF-8 output for Windows console
if sys.stdout and hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

# Add backend directory to sys.path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "backend"))

from app import app, DB_PATH, UPLOADS_DIR

if __name__ == "__main__":
    print("\n=======================================================")
    print("CITIZENSHIELD - SMART CITIZEN SAFETY & CIVIC PORTAL")
    print("=======================================================")
    print(f"* Persistent Database:  {DB_PATH}")
    print(f"* Photo Storage Vault:  {UPLOADS_DIR}")
    print("* Local Access URL:     http://127.0.0.1:5000")
    print("* Production Engine:    Waitress Multi-Threaded WSGI Server")
    print("* Status:               Ready & Listening on port 5000")
    print("=======================================================\n")

    try:
        from waitress import serve
        serve(app, host="0.0.0.0", port=5000, threads=8, channel_timeout=60)
    except ImportError:
        app.run(host="0.0.0.0", port=5000, debug=False, threaded=True)
