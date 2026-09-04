"""
=====================================================================
SIH26001 — Landslide Early Warning System — Backend Server
=====================================================================
Ye backend 3 kaam karta hai:
  1. Risk scores store aur serve karna (map ke liye)
  2. Field reports (citizen/officer se aaye reports) accept karna
  3. Risk score calculate karna (Shivam ke formula ke logic se)

Member: Samiya Khan
Tech: Python + Flask + SQLite
=====================================================================
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import sqlite3
import os
import datetime
import uuid

app = Flask(__name__)
CORS(app)  # Frontend (map/form) kisi bhi domain se is backend ko call kar sake, isliye

DB_PATH = os.path.join(os.path.dirname(__file__), "landslide.db")
UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


# =====================================================================
# DATABASE SETUP
# =====================================================================
def get_db():
    """Har request ke liye ek naya database connection deta hai."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # Rows ko dictionary jaisa access karne dega
    return conn


def init_db():
    """Pehli baar chalane par tables bana deta hai (agar already na ho)."""
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS risk_scores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            area_name TEXT NOT NULL,
            latitude REAL NOT NULL,
            longitude REAL NOT NULL,
            rainfall_mm REAL,
            slope_degree REAL,
            history_score REAL,
            risk_score REAL,
            risk_level TEXT,
            data_source TEXT DEFAULT 'SAMPLE',
            last_updated TEXT
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS field_reports (
            id TEXT PRIMARY KEY,
            reporter_name TEXT,
            reporter_type TEXT,
            latitude REAL NOT NULL,
            longitude REAL NOT NULL,
            observation_type TEXT,
            severity TEXT,
            description TEXT,
            photo_filename TEXT,
            status TEXT DEFAULT 'pending_verification',
            created_at TEXT
        )
    """)

    conn.commit()
    conn.close()


# =====================================================================
# RISK SCORE FORMULA
# (Shivam Rana ke formula ka logic — yahan backend mein bhi rakha hai
#  taaki server khud bhi score calculate kar sake, sirf frontend pe nahi)
# =====================================================================
def calculate_risk_score(rainfall_mm, slope_degree, history_score):
    """
    Teen input leta hai aur 0-100 ka risk score deta hai.

    rainfall_mm     -> pichle 24 ghante ki barish (mm mein)
    slope_degree    -> zameen ka dhalaan (degree mein, 0-90)
    history_score   -> purani landslide history ka score (0-10, jitna zyada utna risky)

    NOTE: Weights abhi ASSUMPTION hain, real calibration ke liye
    Saif Khan ke research data se adjust karna hai.
    """
    # Har factor ko 0-100 scale par normalize karo
    rainfall_component = min(rainfall_mm / 200 * 100, 100)   # 200mm+ = max risk
    slope_component = min(slope_degree / 60 * 100, 100)       # 60 degree+ = max risk
    history_component = min(history_score / 10 * 100, 100)    # 10/10 = max risk

    # Weighted combination (weights: rainfall 40%, slope 35%, history 25%)
    score = (
        rainfall_component * 0.40 +
        slope_component * 0.35 +
        history_component * 0.25
    )
    score = round(min(max(score, 0), 100), 1)

    if score >= 80:
        level = "Critical"
    elif score >= 60:
        level = "High"
    elif score >= 35:
        level = "Moderate"
    else:
        level = "Low"

    return score, level


# =====================================================================
# ROUTES — RISK SCORES
# =====================================================================
@app.route("/api/risk-scores", methods=["GET"])
def get_risk_scores():
    """Sab areas ke risk scores deta hai — map isse call karega."""
    conn = get_db()
    rows = conn.execute("SELECT * FROM risk_scores").fetchall()
    conn.close()
    return jsonify([dict(row) for row in rows])


@app.route("/api/risk-scores", methods=["POST"])
def add_or_update_risk_score():
    """
    Naya area add karta hai ya existing area ka score recalculate karta hai.
    Expected JSON body:
    {
        "area_name": "Thuampui",
        "latitude": 23.7367,
        "longitude": 92.7050,
        "rainfall_mm": 120,
        "slope_degree": 45,
        "history_score": 8,
        "data_source": "GSI research paper"   (optional)
    }
    """
    data = request.get_json()

    required = ["area_name", "latitude", "longitude", "rainfall_mm", "slope_degree", "history_score"]
    missing = [f for f in required if f not in data]
    if missing:
        return jsonify({"error": f"Missing fields: {missing}"}), 400

    score, level = calculate_risk_score(
        data["rainfall_mm"], data["slope_degree"], data["history_score"]
    )

    conn = get_db()
    conn.execute("""
        INSERT INTO risk_scores
        (area_name, latitude, longitude, rainfall_mm, slope_degree, history_score,
         risk_score, risk_level, data_source, last_updated)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        data["area_name"], data["latitude"], data["longitude"],
        data["rainfall_mm"], data["slope_degree"], data["history_score"],
        score, level, data.get("data_source", "SAMPLE"),
        datetime.datetime.now(datetime.timezone.utc).isoformat()
    ))
    conn.commit()
    conn.close()

    return jsonify({"area_name": data["area_name"], "risk_score": score, "risk_level": level}), 201


# =====================================================================
# ROUTES — FIELD REPORTS
# =====================================================================
def is_duplicate_report(conn, lat, lng, observation_type, minutes_window=60):
    """
    Simple duplicate detection: agar isi jagah (0.001 degree ke andar,
    yani ~100m) ka same-type report pichle 'minutes_window' minute mein
    already aa chuka hai, toh ise duplicate maano.
    """
    cutoff = (datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(minutes=minutes_window)).isoformat()
    existing = conn.execute("""
        SELECT id FROM field_reports
        WHERE observation_type = ?
        AND ABS(latitude - ?) < 0.001
        AND ABS(longitude - ?) < 0.001
        AND created_at > ?
    """, (observation_type, lat, lng, cutoff)).fetchone()
    return existing is not None


@app.route("/api/reports", methods=["POST"])
def submit_report():
    """
    Field report submit karta hai. Photo file bhi accept karta hai (multipart/form-data).
    Form fields: reporter_name, reporter_type, latitude, longitude,
                 observation_type, severity, description, photo (file, optional)
    """
    form = request.form
    required = ["latitude", "longitude", "observation_type"]
    missing = [f for f in required if f not in form]
    if missing:
        return jsonify({"error": f"Missing fields: {missing}"}), 400

    lat = float(form["latitude"])
    lng = float(form["longitude"])
    obs_type = form["observation_type"]

    conn = get_db()

    # Spam/duplicate check
    if is_duplicate_report(conn, lat, lng, obs_type):
        conn.close()
        return jsonify({
            "warning": "Similar report already submitted recently from this location.",
            "status": "duplicate_flagged"
        }), 200

    # Photo save karo agar bheja gaya ho
    photo_filename = None
    if "photo" in request.files:
        photo = request.files["photo"]
        if photo.filename:
            ext = os.path.splitext(photo.filename)[1]
            photo_filename = f"{uuid.uuid4().hex}{ext}"
            photo.save(os.path.join(UPLOAD_FOLDER, photo_filename))

    report_id = uuid.uuid4().hex

    conn.execute("""
        INSERT INTO field_reports
        (id, reporter_name, reporter_type, latitude, longitude,
         observation_type, severity, description, photo_filename, status, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        report_id,
        form.get("reporter_name", "Anonymous"),
        form.get("reporter_type", "Citizen"),
        lat, lng, obs_type,
        form.get("severity", "Unknown"),
        form.get("description", ""),
        photo_filename,
        "pending_verification",
        datetime.datetime.now(datetime.timezone.utc).isoformat()
    ))
    conn.commit()
    conn.close()

    return jsonify({"id": report_id, "status": "pending_verification"}), 201


@app.route("/api/reports", methods=["GET"])
def get_reports():
    """Sab field reports deta hai — admin dashboard isse call karega."""
    conn = get_db()
    rows = conn.execute("SELECT * FROM field_reports ORDER BY created_at DESC").fetchall()
    conn.close()
    return jsonify([dict(row) for row in rows])


@app.route("/api/reports/<report_id>/verify", methods=["PATCH"])
def verify_report(report_id):
    """
    Admin/officer isse use karke report ko verify ya reject kar sakta hai.
    Body: {"status": "verified"}  ya  {"status": "rejected"}
    """
    data = request.get_json()
    new_status = data.get("status")
    if new_status not in ["verified", "rejected", "pending_verification"]:
        return jsonify({"error": "Invalid status"}), 400

    conn = get_db()
    conn.execute("UPDATE field_reports SET status = ? WHERE id = ?", (new_status, report_id))
    conn.commit()
    conn.close()
    return jsonify({"id": report_id, "status": new_status})


# =====================================================================
# HEALTH CHECK (deployment verify karne ke liye)
# =====================================================================
@app.route("/", methods=["GET"])
def health():
    return jsonify({"status": "running", "service": "SIH26001 Landslide Backend"})


# =====================================================================
if __name__ == "__main__":
    init_db()
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
