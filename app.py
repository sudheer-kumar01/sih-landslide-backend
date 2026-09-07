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
from werkzeug.security import generate_password_hash, check_password_hash
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired
import sqlite3
import os
import datetime
import uuid

app = Flask(__name__)
CORS(app)  # Frontend (map/form) kisi bhi domain se is backend ko call kar sake, isliye

# NOTE (honesty for judges): ye ek prototype-level secret hai, hardcoded.
# Production mein ye environment variable se aana chahiye, code mein nahi.
SECRET_KEY = "sih26001-prototype-secret-change-in-production"
serializer = URLSafeTimedSerializer(SECRET_KEY)

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
            slope_degree REAL,
            rainfall_24h_mm REAL,
            rainfall_antecedent_mm REAL,
            road_distance_m REAL,
            geology_score REAL,
            landuse_score REAL,
            drainage_score REAL,
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

    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'field_officer',
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
def calculate_risk_score(slope_degree, rainfall_24h_mm, rainfall_antecedent_mm,
                          road_distance_m, geology_score, landuse_score, drainage_score):
    """
    Evidence-based risk score (0-100), built from Saif Khan's verified Aizawl
    research (Barman & Das 2024; Mizoram SDMP 2020; Sangi et al. 2025).

    INPUTS (documented so the team can explain every number to judges):
      slope_degree          -> terrain slope in degrees (0-90).
                                Source: Barman & Das (2024) list slope as a core factor.
      rainfall_24h_mm        -> rainfall in the last 24 hours (mm).
                                Threshold reference: Cyclone Remal recorded 205mm in 24h
                                before the 28 May 2024 Aizawl landslide cluster
                                (Sangi et al. 2025). We use 205mm as our "high trigger"
                                reference point -- NOT a universal threshold, just the
                                one real documented Aizawl trigger event we have.
      rainfall_antecedent_mm -> rainfall in the preceding 3-4 days (mm), captures soil
                                saturation build-up. Sangi et al. 2025 record the
                                24-28 May 2024 sequence: 2.2, 8.2, 21.8, 80mm before
                                the 205mm trigger day.
      road_distance_m        -> distance of the location from the nearest road (metres).
                                Barman & Das (2024) report distance-to-road as the
                                HIGHEST predictive factor in their Aizawl model
                                (closer to road/road-cutting = higher risk).
      geology_score          -> 0-10 rating of geological/lithological weakness
                                (fractured/weak rock = higher score). Source: geology
                                repeatedly linked to slope instability in Aizawl studies.
      landuse_score           -> 0-10 rating of human modification / land-use disturbance.
      drainage_score          -> 0-10 rating of poor drainage / wetness (TWI proxy).

    IMPORTANT (do not remove this note): The WEIGHTS below are our own prototype
    assumption, built from the relative "priority tier" Saif's research assigned
    to each factor (High priority: slope, rainfall, geology, road-distance;
    Medium-high: land use, drainage). These are NOT the exact numeric weights from
    any single paper -- the old local case-study weights (9-8-7-6-5-4) are
    explicitly flagged in the research pack as study-specific, not official.
    If asked by judges: "Weights are our prototype design, informed by which
    factors the Aizawl literature repeatedly identifies as important -- final
    calibration needs a larger validated dataset."
    """
    slope_component = min(slope_degree / 60 * 100, 100)

    # Rainfall trigger: scaled against the one real documented Aizawl trigger (205mm/24h)
    rainfall_trigger = min(rainfall_24h_mm / 205 * 100, 100)
    # Antecedent rainfall adds saturation risk, capped at 100
    antecedent_component = min(rainfall_antecedent_mm / 100 * 100, 100)
    rainfall_component = (rainfall_trigger * 0.7) + (antecedent_component * 0.3)

    # Closer to road = higher risk (within 500m = max, per Barman & Das road-proximity finding)
    road_component = max(0, 100 - min(road_distance_m / 500 * 100, 100))

    geology_component = min(geology_score / 10 * 100, 100)
    landuse_component = min(landuse_score / 10 * 100, 100)
    drainage_component = min(drainage_score / 10 * 100, 100)

    score = (
        rainfall_component * 0.30 +
        slope_component * 0.20 +
        road_component * 0.15 +
        geology_component * 0.15 +
        landuse_component * 0.10 +
        drainage_component * 0.10
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
# AUTHENTICATION (prototype-level — hashed passwords, signed tokens)
# =====================================================================
def get_current_user():
    """
    Authorization header se token nikalta hai aur verify karta hai.
    Return: {"username":..., "role":...} ya None (invalid/missing token)
    """
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        return None
    token = auth_header.replace("Bearer ", "")
    try:
        data = serializer.loads(token, max_age=86400)  # 24 ghante valid
        return data
    except (BadSignature, SignatureExpired):
        return None


@app.route("/api/auth/signup", methods=["POST"])
def signup():
    data = request.get_json()
    username = (data.get("username") or "").strip()
    password = data.get("password") or ""
    role = data.get("role") or "field_officer"

    if len(username) < 3 or len(password) < 6:
        return jsonify({"error": "Username must be 3+ chars, password 6+ chars"}), 400
    if role not in ["field_officer", "authority"]:
        return jsonify({"error": "Invalid role"}), 400

    conn = get_db()
    existing = conn.execute("SELECT id FROM users WHERE username = ?", (username,)).fetchone()
    if existing:
        conn.close()
        return jsonify({"error": "Username already taken"}), 409

    password_hash = generate_password_hash(password)
    conn.execute(
        "INSERT INTO users (username, password_hash, role, created_at) VALUES (?, ?, ?, ?)",
        (username, password_hash, role, datetime.datetime.now(datetime.timezone.utc).isoformat())
    )
    conn.commit()
    conn.close()
    return jsonify({"message": "Account created. Please log in."}), 201


@app.route("/api/auth/login", methods=["POST"])
def login():
    data = request.get_json()
    username = (data.get("username") or "").strip()
    password = data.get("password") or ""

    conn = get_db()
    user = conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
    conn.close()

    if not user or not check_password_hash(user["password_hash"], password):
        return jsonify({"error": "Invalid username or password"}), 401

    token = serializer.dumps({"username": user["username"], "role": user["role"]})
    return jsonify({"token": token, "username": user["username"], "role": user["role"]})


@app.route("/api/auth/me", methods=["GET"])
def me():
    user = get_current_user()
    if not user:
        return jsonify({"error": "Not logged in"}), 401
    return jsonify(user)


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
        "area_name": "Laipuitlang",
        "latitude": 23.735, "longitude": 92.725,
        "slope_degree": 45,
        "rainfall_24h_mm": 120,
        "rainfall_antecedent_mm": 60,
        "road_distance_m": 200,
        "geology_score": 7,
        "landuse_score": 6,
        "drainage_score": 5,
        "data_source": "Barman & Das 2024 + Mizoram SDMP 2020"   (optional but recommended)
    }
    """
    data = request.get_json()

    required = ["area_name", "latitude", "longitude", "slope_degree", "rainfall_24h_mm",
                "rainfall_antecedent_mm", "road_distance_m", "geology_score",
                "landuse_score", "drainage_score"]
    missing = [f for f in required if f not in data]
    if missing:
        return jsonify({"error": f"Missing fields: {missing}"}), 400

    score, level = calculate_risk_score(
        data["slope_degree"], data["rainfall_24h_mm"], data["rainfall_antecedent_mm"],
        data["road_distance_m"], data["geology_score"], data["landuse_score"],
        data["drainage_score"]
    )

    conn = get_db()
    conn.execute("""
        INSERT INTO risk_scores
        (area_name, latitude, longitude, slope_degree, rainfall_24h_mm, rainfall_antecedent_mm,
         road_distance_m, geology_score, landuse_score, drainage_score,
         risk_score, risk_level, data_source, last_updated)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        data["area_name"], data["latitude"], data["longitude"],
        data["slope_degree"], data["rainfall_24h_mm"], data["rainfall_antecedent_mm"],
        data["road_distance_m"], data["geology_score"], data["landuse_score"], data["drainage_score"],
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
    Ab LOGIN ZAROORI hai — sirf field_officer/authority role wale hi
    verify/reject kar sakte hain, taaki koi bhi random request se report
    status change na kar sake.
    Body: {"status": "verified"}  ya  {"status": "rejected"}
    """
    user = get_current_user()
    if not user:
        return jsonify({"error": "Login required to verify reports"}), 401

    data = request.get_json()
    new_status = data.get("status")
    if new_status not in ["verified", "rejected", "pending_verification"]:
        return jsonify({"error": "Invalid status"}), 400

    conn = get_db()
    conn.execute("UPDATE field_reports SET status = ? WHERE id = ?", (new_status, report_id))
    conn.commit()
    conn.close()
    return jsonify({"id": report_id, "status": new_status, "verified_by": user["username"]})


# =====================================================================
# HEALTH CHECK (deployment verify karne ke liye)
# =====================================================================
@app.route("/", methods=["GET"])
def health():
    return jsonify({"status": "running", "service": "SIH26001 Landslide Backend"})


# =====================================================================
# =====================================================================
# Database table hamesha bana do jab bhi ye file import ho —
# (chahe 'python app.py' se chale, chahe gunicorn se — Render gunicorn
#  use karta hai, jo __main__ block kabhi nahi chalata)
# =====================================================================
init_db()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
