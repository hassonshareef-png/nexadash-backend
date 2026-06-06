from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
import hashlib, jwt, numpy as np
from datetime import datetime, timedelta

SECRET_KEY = "nexadash-secret-2026"
ALGORITHM = "HS256"
TOKEN_EXPIRE_MINUTES = 60

USERS = {
    "admin": {"hash": "99051091580170494132cc07c5bfbd956bdce00ebc0ceded5808316d3efa3ffc", "plan": "Enterprise"},
    "hass":  {"hash": "99051091580170494132cc07c5bfbd956bdce00ebc0ceded5808316d3efa3ffc", "plan": "Pro"},
}

app = FastAPI(title="NexaDash API", version="1.5.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login/form")

class LoginRequest(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str
    username: str
    plan: str

def _sha256(pw): return hashlib.sha256(pw.encode()).hexdigest()
def _create_token(data):
    p = data.copy(); p["exp"] = datetime.utcnow() + timedelta(minutes=TOKEN_EXPIRE_MINUTES)
    return jwt.encode(p, SECRET_KEY, algorithm=ALGORITHM)
def _verify_token(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        u = payload.get("sub")
        if not u or u not in USERS: raise HTTPException(status_code=401, detail="Invalid token")
        return u
    except jwt.ExpiredSignatureError: raise HTTPException(status_code=401, detail="Token expired")
    except jwt.PyJWTError: raise HTTPException(status_code=401, detail="Invalid token")

@app.get("/")
def root(): return {"message": "NexaDash API running", "docs": "/docs"}

@app.get("/health")
def health(): return {"status": "ok", "version": "1.5.0", "timestamp": datetime.utcnow().isoformat()}

@app.post("/auth/login", response_model=Token)
def login(body: LoginRequest):
    user = USERS.get(body.username)
    if not user or user["hash"] != _sha256(body.password): raise HTTPException(status_code=401, detail="Invalid credentials")
    return Token(access_token=_create_token({"sub": body.username}), token_type="bearer", username=body.username, plan=user["plan"])

@app.post("/auth/login/form", response_model=Token)
def login_form(form: OAuth2PasswordRequestForm = Depends()):
    user = USERS.get(form.username)
    if not user or user["hash"] != _sha256(form.password): raise HTTPException(status_code=401, detail="Invalid credentials")
    return Token(access_token=_create_token({"sub": form.username}), token_type="bearer", username=form.username, plan=user["plan"])

@app.get("/api/user/me")
def get_me(u: str = Depends(_verify_token)):
    return {"username": u, "plan": USERS[u]["plan"], "email": f"{u}@nexadash.io", "name": u.capitalize()}

@app.get("/api/notifications")
def get_notifications(u: str = Depends(_verify_token)):
    return {"count": 3, "items": [
        {"id": 1, "message": "Revenue target reached for Q2", "type": "success", "time": "2h ago"},
        {"id": 2, "message": "2 server alerts need attention", "type": "warning", "time": "4h ago"},
        {"id": 3, "message": "New enterprise client signed", "type": "info", "time": "1d ago"},
    ]}

@app.get("/api/metrics")
def get_metrics(u: str = Depends(_verify_token)):
    return {
        "revenue": {"value": "$84,320", "change": "+12.4%"},
        "active_users": {"value": "14,892", "change": "+8.1%"},
        "conversion": {"value": "3.72%", "change": "+0.5%"},
        "avg_session": {"value": "4m 12s", "change": "+22s"},
        "uptime": {"value": "99.97%", "change": "+0.01%"},
    }

@app.get("/api/revenue")
def get_revenue(days: int = 30, u: str = Depends(_verify_token)):
    np.random.seed(42)
    revenue = (np.cumsum(np.random.randint(2000, 5000, days)) + 40000).tolist()
    target = np.linspace(revenue[0], revenue[-1] * 1.1, days).tolist()
    return {"days": list(range(1, days+1)), "revenue": [round(v,2) for v in revenue], "target": [round(v,2) for v in target]}

@app.get("/api/transactions")
def get_transactions(u: str = Depends(_verify_token)):
    return {"transactions": [
        {"date": "Jun 1",  "user": "Alice M.",  "plan": "Pro",     "amount": "$2,450", "status": "Completed"},
        {"date": "May 31", "user": "Bob K.",    "plan": "Team",    "amount": "$1,980", "status": "Completed"},
        {"date": "May 31", "user": "Carol T.",  "plan": "Pro",     "amount": "$2,450", "status": "Processing"},
        {"date": "May 30", "user": "Dan R.",    "plan": "Starter", "amount": "$499",   "status": "Completed"},
        {"date": "May 29", "user": "Eve S.",    "plan": "Team",    "amount": "$1,980", "status": "Completed"},
    ]}

@app.get("/api/traffic")
def get_traffic(u: str = Depends(_verify_token)):
    return {"sources": ["Organic","Paid","Referral","Social","Direct"], "values": [38,27,15,12,8]}

@app.get("/api/analytics")
def get_analytics(days: int = 30, u: str = Depends(_verify_token)):
    np.random.seed(42)
    dau = np.random.randint(8000, 16000, days).tolist()
    return {
        "days": list(range(1, days+1)), "dau": dau,
        "retention": {"weeks": ["Wk1","Wk2","Wk3","Wk4"], "values": [100,68,52,43]},
        "metrics": {
            "bounce_rate": {"value": "42.3%", "change": "-2.1%"},
            "avg_page_load": {"value": "1.23s", "change": "-0.15s"},
            "mobile_traffic": {"value": "68%", "change": "+5.2%"},
        },
    }

@app.get("/api/projects")
def get_projects(u: str = Depends(_verify_token)):
    return {"projects": [
        {"name": "NexaDash v2.0",      "progress": 78, "status": "On Track",    "color": "green"},
        {"name": "Mobile Redesign",     "progress": 45, "status": "In Progress", "color": "yellow"},
        {"name": "API Integration",     "progress": 91, "status": "Almost Done", "color": "green"},
        {"name": "Marketing Campaign",  "progress": 33, "status": "Delayed",     "color": "red"},
        {"name": "Data Pipeline",       "progress": 60, "status": "On Track",    "color": "green"},
    ]}

@app.get("/api/reports")
def get_reports(report_type: str = "Revenue Summary", u: str = Depends(_verify_token)):
    return {
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
    }
