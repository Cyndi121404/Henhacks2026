"""
Hen-tersection.py
=================
Snowflake backend + Flask API proxy for the Hen-Tersection Smart Crosswalk System.

INSTALL DEPENDENCIES FIRST:
    pip install snowflake-connector-python flask flask-cors

RUN:
    python Hen-tersection.py

The server starts on http://localhost:5050
Then open index.html -> Admin -> Snowflake -> enter account -> toggle on -> Save Config
"""

import base64
import io
import json
import uuid
import sys
from datetime import datetime, timezone

# ─────────────────────────────────────────────────────────────────────────────
# CHECK DEPENDENCIES
# ─────────────────────────────────────────────────────────────────────────────
def check_dependencies():
    missing = []
    try:
        import snowflake.connector
    except ImportError:
        missing.append("snowflake-connector-python")
    try:
        import flask
    except ImportError:
        missing.append("flask")
    try:
        import flask_cors
    except ImportError:
        missing.append("flask-cors")

    if missing:
        print("=" * 60)
        print("ERROR - Missing required packages:")
        for pkg in missing:
            print(f"  - {pkg}")
        print("\nFix by running:")
        print(f"  pip install {' '.join(missing)}")
        print("=" * 60)
        sys.exit(1)

check_dependencies()

import snowflake.connector
from snowflake.connector import DictCursor
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS

# ─────────────────────────────────────────────────────────────────────────────
# SNOWFLAKE CONNECTION CONFIG
# ─────────────────────────────────────────────────────────────────────────────
CONFIG = {
    "user":       "CYNDISANCHEZ",
    "password":   "TalishaMalik224!",
    "account":    "IPMGUFF-RM98977",
    "warehouse":  "CROSSWALK_WH",
    "database":   "SMART_CITY",
    "schema":     "TRAFFIC_LOGS",
    "role":       "ACCOUNTADMIN",
    "autocommit": True,
}

ACCOUNT_FORMATS = [
    "IPMGUFF-RM98977",
    "ipmguff-rm98977",
    "IPMGUFF.RM98977",
    "ipmguff.rm98977",
    "RM98977",
    "rm98977",
]

# ─────────────────────────────────────────────────────────────────────────────
# FLASK APP
# ─────────────────────────────────────────────────────────────────────────────
app = Flask(__name__)
CORS(app)

# ─────────────────────────────────────────────────────────────────────────────
# SNOWFLAKE CONNECTION HELPER
# ─────────────────────────────────────────────────────────────────────────────
def get_connection():
    last_error = None
    for account_fmt in ACCOUNT_FORMATS:
        try:
            conn = snowflake.connector.connect(
                user=CONFIG["user"],
                password=CONFIG["password"],
                account=account_fmt,
                warehouse=CONFIG["warehouse"],
                database=CONFIG["database"],
                schema=CONFIG["schema"],
                role=CONFIG["role"],
                autocommit=CONFIG["autocommit"],
                login_timeout=15,
            )
            CONFIG["account"] = account_fmt
            return conn
        except Exception as e:
            last_error = e
            continue

    print("\n" + "=" * 60)
    print("ERROR - Could not connect to Snowflake.")
    print("Last error:", last_error)
    print("=" * 60 + "\n")
    raise last_error

# ─────────────────────────────────────────────────────────────────────────────
# CONNECTION TEST
# ─────────────────────────────────────────────────────────────────────────────
def test_connection():
    print("\nTesting Snowflake connection...")
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT CURRENT_USER(), CURRENT_ACCOUNT(), CURRENT_TIMESTAMP()")
        row = cur.fetchone()
        conn.close()
        print(f"  OK - Connected as user={row[0]}  account={row[1]}  time={row[2]}")
        return True
    except Exception as e:
        print(f"  FAILED - {e}")
        return False

# ─────────────────────────────────────────────────────────────────────────────
# SCHEMA SETUP  (runs on startup)
# ─────────────────────────────────────────────────────────────────────────────
def setup_schema():
    """Create tables if they don't already exist (preserves existing data)."""
    statements = [
        "USE WAREHOUSE CROSSWALK_WH",
        "USE DATABASE SMART_CITY",
        "USE SCHEMA TRAFFIC_LOGS",

        # Pedestrian crossings table
        """
        CREATE TABLE IF NOT EXISTS CROSSING_LOGS (
            event_id           STRING        NOT NULL DEFAULT uuid_string(),
            timestamp          TIMESTAMP_NTZ NOT NULL DEFAULT current_timestamp(),
            pedestrian_type    STRING,
            duration_seconds   FLOAT,
            was_light_extended BOOLEAN,
            persons_count      INT,
            confidence_pct     FLOAT,
            notes              TEXT
        )
        """,

        # Jaywalking violations table
        """
        CREATE TABLE IF NOT EXISTS JAYWALKING_VIOLATIONS (
            violation_id   STRING        NOT NULL DEFAULT uuid_string(),
            timestamp      TIMESTAMP_NTZ NOT NULL DEFAULT current_timestamp(),
            severity       STRING,
            description    TEXT,
            image_data     TEXT,
            image_filename STRING,
            pedestrian_id  STRING,
            location       STRING DEFAULT 'Hen-Tersection Unit'
        )
        """,

        # App settings / config persistence table
        """
        CREATE TABLE IF NOT EXISTS APP_SETTINGS (
            setting_key    STRING NOT NULL,
            setting_value  TEXT,
            updated_at     TIMESTAMP_NTZ NOT NULL DEFAULT current_timestamp(),
            PRIMARY KEY (setting_key)
        )
        """,
    ]

    conn = get_connection()
    try:
        cur = conn.cursor()
        for stmt in statements:
            cur.execute(stmt.strip())
        print("  OK - Tables ready.")
    except Exception as e:
        print(f"  ERROR - Schema setup failed: {e}")
        raise
    finally:
        conn.close()

# ─────────────────────────────────────────────────────────────────────────────
# CROSSING LOG
# ─────────────────────────────────────────────────────────────────────────────
def log_crossing(pedestrian_type, duration_seconds, was_light_extended,
                 persons_count=1, confidence_pct=None, notes=""):
    event_id = str(uuid.uuid4())
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    sql = """
        INSERT INTO CROSSING_LOGS
            (event_id, timestamp, pedestrian_type, duration_seconds,
             was_light_extended, persons_count, confidence_pct, notes)
        VALUES (%s, %s::TIMESTAMP_NTZ, %s, %s, %s, %s, %s, %s)
    """
    conn = get_connection()
    try:
        conn.cursor().execute(sql, (
            event_id, ts, pedestrian_type, duration_seconds,
            was_light_extended, persons_count, confidence_pct, notes,
        ))
        print(f"[crossing]  OK - {pedestrian_type} at {ts}")
        return event_id
    finally:
        conn.close()

# ─────────────────────────────────────────────────────────────────────────────
# JAYWALKING VIOLATIONS
# ─────────────────────────────────────────────────────────────────────────────
def log_jaywalking_violation_from_dataurl(severity, description, data_url=None,
                                          pedestrian_id=None, location="Hen-Tersection Unit"):
    violation_id = str(uuid.uuid4())
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    image_b64 = None
    image_filename = f"jaywalk-violation-{int(datetime.now().timestamp() * 1000)}.png"

    if data_url and data_url.startswith("data:"):
        header, b64data = data_url.split(",", 1)
        ext = "png" if "png" in header else "jpg"
        image_filename = f"jaywalk-violation-{int(datetime.now().timestamp() * 1000)}.{ext}"
        image_b64 = b64data

    sql = """
        INSERT INTO JAYWALKING_VIOLATIONS
            (violation_id, timestamp, severity, description,
             image_data, image_filename, pedestrian_id, location)
        VALUES (%s, %s::TIMESTAMP_NTZ, %s, %s, %s, %s, %s, %s)
    """
    conn = get_connection()
    try:
        conn.cursor().execute(sql, (
            violation_id, ts, severity, description,
            image_b64, image_filename, pedestrian_id, location,
        ))
        print(f"[jaywalk]   OK - {severity} at {ts}")
        return violation_id
    finally:
        conn.close()

# ─────────────────────────────────────────────────────────────────────────────
# SETTINGS PERSISTENCE
# ─────────────────────────────────────────────────────────────────────────────
def get_settings(key="app_settings"):
    sql = "SELECT setting_value FROM APP_SETTINGS WHERE setting_key = %s LIMIT 1"
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(sql, (key,))
        row = cur.fetchone()
        if row and row[0]:
            return json.loads(row[0])
        return {}
    finally:
        conn.close()

def save_settings(data, key="app_settings"):
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    value = json.dumps(data)
    # MERGE: update if exists, insert if not
    sql = """
        MERGE INTO APP_SETTINGS AS target
        USING (SELECT %s AS setting_key, %s AS setting_value, %s::TIMESTAMP_NTZ AS updated_at) AS src
        ON target.setting_key = src.setting_key
        WHEN MATCHED THEN UPDATE SET setting_value = src.setting_value, updated_at = src.updated_at
        WHEN NOT MATCHED THEN INSERT (setting_key, setting_value, updated_at)
            VALUES (src.setting_key, src.setting_value, src.updated_at)
    """
    conn = get_connection()
    try:
        conn.cursor().execute(sql, (key, value, ts))
        print(f"[settings]  OK - saved key={key}")
    finally:
        conn.close()

# ─────────────────────────────────────────────────────────────────────────────
# QUERIES
# ─────────────────────────────────────────────────────────────────────────────
def get_recent_violations(limit=50):
    sql = """
        SELECT
            violation_id,
            TO_CHAR(timestamp, 'YYYY-MM-DD HH24:MI:SS') AS timestamp,
            severity, description, image_filename, pedestrian_id, location
        FROM JAYWALKING_VIOLATIONS
        ORDER BY timestamp DESC LIMIT %s
    """
    conn = get_connection()
    try:
        cur = conn.cursor(DictCursor)
        cur.execute(sql, (limit,))
        return [dict(r) for r in cur.fetchall()]
    finally:
        conn.close()

def get_violation_image(violation_id):
    sql = """
        SELECT image_data, image_filename FROM JAYWALKING_VIOLATIONS
        WHERE violation_id = %s LIMIT 1
    """
    conn = get_connection()
    try:
        cur = conn.cursor(DictCursor)
        cur.execute(sql, (violation_id,))
        row = cur.fetchone()
        if not row or not row.get("IMAGE_DATA"):
            return None, None
        image_bytes = base64.b64decode(row["IMAGE_DATA"])
        return image_bytes, row.get("IMAGE_FILENAME", "violation.png")
    finally:
        conn.close()

def get_recent_crossings(limit=100):
    sql = """
        SELECT
            event_id,
            TO_CHAR(timestamp, 'YYYY-MM-DD HH24:MI:SS') AS timestamp,
            pedestrian_type, duration_seconds, was_light_extended,
            persons_count, confidence_pct, notes
        FROM CROSSING_LOGS
        ORDER BY timestamp DESC LIMIT %s
    """
    conn = get_connection()
    try:
        cur = conn.cursor(DictCursor)
        cur.execute(sql, (limit,))
        return [dict(r) for r in cur.fetchall()]
    finally:
        conn.close()

# ─────────────────────────────────────────────────────────────────────────────
# FLASK API ROUTES
# ─────────────────────────────────────────────────────────────────────────────

@app.route("/api/snowflake", methods=["POST"])
def api_snowflake():
    payload = request.get_json(force=True)
    table   = payload.get("table", "").upper()
    record  = payload.get("record", {})

    try:
        if table == "CROSSING_LOGS":
            event_id = log_crossing(
                pedestrian_type    = record.get("pedestrian_type", "normal"),
                duration_seconds   = record.get("duration_seconds", 0),
                was_light_extended = record.get("was_light_extended", False),
                persons_count      = record.get("persons_count", 1),
                confidence_pct     = record.get("confidence_pct"),
                notes              = record.get("notes", ""),
            )
            return jsonify({"ok": True, "event_id": event_id})

        elif table == "JAYWALKING_VIOLATIONS":
            violation_id = log_jaywalking_violation_from_dataurl(
                severity      = record.get("severity", "WARNING"),
                description   = record.get("description", ""),
                data_url      = record.get("image_dataurl"),
                pedestrian_id = str(record.get("pedestrian_id", "")),
                location      = record.get("location", "Hen-Tersection Unit"),
            )
            return jsonify({"ok": True, "violation_id": violation_id})

        else:
            return jsonify({"ok": False, "error": f"Unknown table: {table}"}), 400

    except Exception as exc:
        print(f"[api_snowflake] ERROR: {exc}")
        return jsonify({"ok": False, "error": str(exc)}), 500


@app.route("/api/settings", methods=["GET"])
def api_get_settings():
    """Return persisted app settings from Snowflake."""
    key = request.args.get("key", "app_settings")
    try:
        data = get_settings(key)
        return jsonify({"ok": True, "settings": data})
    except Exception as exc:
        return jsonify({"ok": False, "error": str(exc)}), 500


@app.route("/api/settings", methods=["POST"])
def api_save_settings():
    """Persist app settings to Snowflake."""
    payload = request.get_json(force=True)
    key     = payload.get("key", "app_settings")
    data    = payload.get("settings", {})
    try:
        save_settings(data, key)
        return jsonify({"ok": True})
    except Exception as exc:
        return jsonify({"ok": False, "error": str(exc)}), 500


@app.route("/api/violations", methods=["GET"])
def api_violations():
    limit = int(request.args.get("limit", 50))
    try:
        return jsonify(get_recent_violations(limit))
    except Exception as exc:
        return jsonify({"ok": False, "error": str(exc)}), 500


@app.route("/api/violations/<violation_id>/image", methods=["GET"])
def api_violation_image(violation_id):
    try:
        image_bytes, filename = get_violation_image(violation_id)
        if not image_bytes:
            return jsonify({"error": "Image not found"}), 404
        return send_file(
            io.BytesIO(image_bytes),
            mimetype="image/png",
            as_attachment=True,
            download_name=filename,
        )
    except Exception as exc:
        return jsonify({"ok": False, "error": str(exc)}), 500


@app.route("/api/crossings", methods=["GET"])
def api_crossings():
    limit = int(request.args.get("limit", 100))
    try:
        return jsonify(get_recent_crossings(limit))
    except Exception as exc:
        return jsonify({"ok": False, "error": str(exc)}), 500


@app.route("/api/health", methods=["GET"])
def api_health():
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT CURRENT_USER(), CURRENT_ACCOUNT(), CURRENT_TIMESTAMP()")
        row = cur.fetchone()
        conn.close()
        return jsonify({"ok": True, "status": "Snowflake connected",
                        "user": row[0], "account": row[1], "time": str(row[2])})
    except Exception as exc:
        return jsonify({"ok": False, "status": f"Snowflake error: {exc}"}), 500


# ─────────────────────────────────────────────────────────────────────────────
# ENTRY POINT
# ─────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("=" * 60)
    print("  Hen-Tersection  |  Snowflake Backend")
    print("=" * 60)

    if not test_connection():
        print("\nCould not connect to Snowflake. Fix the error above and try again.")
        sys.exit(1)

    print("\nSetting up Snowflake schema...")
    setup_schema()

    print("\nStarting Flask API server on http://localhost:5050")
    print("")
    print("  POST /api/snowflake              <-- log crossings & violations")
    print("  GET  /api/violations             <-- list recent violations")
    print("  GET  /api/violations/<id>/image  <-- download a violation photo")
    print("  GET  /api/crossings              <-- list recent crossings")
    print("  GET  /api/settings               <-- get persisted settings")
    print("  POST /api/settings               <-- save settings to Snowflake")
    print("  GET  /api/health                 <-- check Snowflake connection")
    print("")
    print("Keep this window open while index.html is running.")
    print("=" * 60 + "\n")

    app.run(host="0.0.0.0", port=5050, debug=False)
