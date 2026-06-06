from flask import Flask, request, jsonify
from functools import wraps
import hashlib, jwt, numpy as np
from datetime import datetime, timedelta

SECRET_KEY = "nexadash-secret-2026"
ALGORITHM  = "HS256"
TOKEN_EXPIRE_MINUTES = 60

USERS = {
    "admin": {"hash": "99051091580170494132cc07c5bfbd956bdce00ebc0ceded5808316d3efa3ffc", "plan": "Enterprise"},
    "hass":  {"hash": "99051091580170494132cc07c5bfbd956bdce00ebc0ceded5808316d3efa3ffc", "plan": "Pro"},
}

app = Flask(__name__)

def _sha256(pw):
    return hashlib.sha256(pw.encode()).hexdigest()

def _create_token(username):
    payload = {"sub": username, "exp": datetime.utcnow() + timedelta(minutes=TOKEN_EXPIRE_MINUTES)}
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

def _verify_token(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.headers.get("Authorization", "")
        if not auth.startswith("Bearer "):
            return jsonify({"error": "Missing token"}), 401
        token = auth.split(" ", 1)[1]
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            username = payload.get("sub")
            if not username or username not in USERS:
                return jsonify({"error": "Invalid token"}), 401
            request.username = username
        except jwt.ExpiredSignatureError:
            return jsonify({"error": "Token expired"}), 401
        except jwt.PyJWTError:
            return jsonify({"error": "Invalid token"}), 401
        return f(*args, **kwargs)
    return decorated

@app.after_request
def add_cors(response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Headers"] = "Authorization, Content-Type"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    return response

@app.route("/", methods=["GET"])
def root():
    return jsonify({"message": "NexaDash API running", "docs": "/health", "version": "1.5.0"})

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "version": "1.5.0", "timestamp": datetime.utcnow().isoformat()})

@app.route("/auth/login", methods=["POST", "OPTIONS"])
def login():
    if request.method == "OPTIONS":
        return jsonify({}), 200
    data = request.get_json() or {}
    username = data.get("username", "")
    password = data.get("password", "")
    user = USERS.get(username)
    if not user or user["hash"] != _sha256(password):
        return jsonify({"error": "Invalid credentials"}), 401
    token = _create_token(username)
    return jsonify({"access_token": token, "token_type": "bearer", "username": username, "plan": user["plan"]})

@app.route("/api/user/me", methods=["GET"])
@_verify_token
def get_me():
    u = request.username
    return jsonify({"username": u, "plan": USERS[u]["plan"], "email": f"{u}@nexadash.io", "name": u.capitalize()})

@app.route("/api/notifications", methods=["GET"])
@_verify_token
def get_notifications():
    return jsonify({"count": 3, "items": [
        {"id": 1, "message": "Revenue target reached for Q2", "type": "success", "time": "2h ago"},
        {"id": 2, "message": "2 server alerts need attention",  "type": "warning", "time": "4h ago"},
        {"id": 3, "message": "New enterprise client signed",    "type": "info",    "time": "1d ago"},
    ]})

@app.route("/api/metrics", methods=["GET"])
@_verify_token
def get_metrics():
    return jsonify({
        "revenue":      {"value": "$84,320", "change": "+12.4%"},
        "active_users": {"value": "14,892",  "change": "+8.1%"},
        "conversion":   {"value": "3.72%",   "change": "+0.5%"},
        "avg_session":  {"value": "4m 12s",  "change": "+22s"},
        "uptime":       {"value": "99.97%",  "change": "+0.01%"},
    })

@app.route("/api/revenue", methods=["GET"])
@_verify_token
def get_revenue():
    days = int(request.args.get("days", 30))
    np.random.seed(42)
    revenue = (np.cumsum(np.random.randint(2000, 5000, days)) + 40000).tolist()
    target  = np.linspace(revenue[0], revenue[-1] * 1.1, days).tolist()
    return jsonify({"days": list(range(1, days+1)), "revenue": [round(v,2) for v in revenue], "target": [round(v,2) for v in target]})

@app.route("/api/transactions", methods=["GET"])
@_verify_token
def get_transactions():
    return jsonify({"transactions": [
        {"date": "Jun 1",  "user": "Alice M.",  "plan": "Pro",     "amount": "$2,450", "status": "Completed"},
        {"date": "May 31", "user": "Bob K.",    "plan": "Team",    "amount": "$1,980", "status": "Completed"},
        {"date": "May 31", "user": "Carol T.",  "plan": "Pro",     "amount": "$2,450", "status": "Processing"},
        {"date": "May 30", "user": "Dan R.",    "plan": "Starter", "amount": "$499",   "status": "Completed"},
        {"date": "May 29", "user": "Eve S.",    "plan": "Team",    "amount": "$1,980", "status": "Completed"},
    ]})

@app.route("/api/traffic", methods=["GET"])
@_verify_token
def get_traffic():
    return jsonify({"sources": ["Organic","Paid","Referral","Social","Direct"], "values": [38,27,15,12,8]})

@app.route("/api/analytics", methods=["GET"])
@_verify_token
def get_analytics():
    days = int(request.args.get("days", 30))
    np.random.seed(42)
    dau = np.random.randint(8000, 16000, days).tolist()
    return jsonify({
        "days": list(range(1, days+1)), "dau": dau,
        "retention": {"weeks": ["Wk1","Wk2","Wk3","Wk4"], "values": [100,68,52,43]},
        "metrics": {
            "bounce_rate":    {"value": "42.3%", "change": "-2.1%"},
            "avg_page_load":  {"value": "1.23s", "change": "-0.15s"},
            "mobile_traffic": {"value": "68%",   "change": "+5.2%"},
        },
    })

@app.route("/api/projects", methods=["GET"])
@_verify_token
def get_projects():
    return jsonify({"projects": [
        {"name": "NexaDash v2.0",      "progress": 78, "status": "On Track",    "color": "green"},
        {"name": "Mobile Redesign",     "progress": 45, "status": "In Progress", "color": "yellow"},
        {"name": "API Integration",     "progress": 91, "status": "Almost Done", "color": "green"},
        {"name": "Marketing Campaign",  "progress": 33, "status": "Delayed",     "color": "red"},
        {"name": "Data Pipeline",       "progress": 60, "status": "On Track",    "color": "green"},
    ]})

@app.route("/api/reports", methods=["GET"])
@_verify_token
def get_reports():
    report_type = request.args.get("report_type", "Revenue Summary")
    return jsonify({
        "report_type": report_type, "generated_at": datetime.utcnow().isoformat(),
        "summary": [
            {"metric": "Revenue",    "current": "$84,320", "previous": "$75,100", "change": "+12.4%"},
            {"metric": "Users",      "current": "14,892",  "previous": "13,750",  "change": "+8.1%"},
            {"metric": "Conversion", "current": "3.72%",   "previous": "3.45%",   "change": "+0.27%"},
            {"metric": "Uptime",     "current": "99.97%",  "previous": "99.95%",  "change": "+0.02%"},
        ],
        "analysis": [
            "Revenue increased significantly due to new enterprise clients",
            "User growth is consistent with marketing campaigns",
            "Conversion rate improved with recent UI updates",
            "System uptime remains excellent at 99.97% availability",
        ],
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
