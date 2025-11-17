import os
from datetime import datetime
from typing import Dict, Any, List, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from database import db, create_document, get_documents

app = FastAPI(title="Designer Growth Platform API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {"message": "Designer Growth Platform API running"}

@app.get("/test")
def test_database():
    info = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "collections": []
    }
    try:
        if db is not None:
            info["database"] = "✅ Connected"
            info["collections"] = db.list_collection_names()
        else:
            info["database"] = "❌ Not Connected"
    except Exception as e:
        info["database"] = f"⚠️ {str(e)[:120]}"
    return info

# -------- Reference data --------
COMPETENCIES = [
    {"key": "product_strategy", "title": "Product Strategy"},
    {"key": "craft_quality", "title": "Craft Quality"},
    {"key": "collaboration", "title": "Collaboration"},
    {"key": "impact", "title": "Impact"},
    {"key": "mentorship", "title": "Mentorship"},
]

CAREER_LEVELS = [
    {"level": "Junior", "expectations": {
        "craft_quality": "Executes with guidance",
        "collaboration": "Communicates within team",
        "impact": "Delivers assigned tasks",
    }},
    {"level": "Mid", "expectations": {
        "product_strategy": "Contributes to product thinking",
        "craft_quality": "Owns features end-to-end",
        "collaboration": "Works cross-functionally",
        "impact": "Improves team outcomes",
    }},
    {"level": "Senior", "expectations": {
        "product_strategy": "Shapes problem spaces",
        "craft_quality": "Raises quality bar",
        "collaboration": "Aligns stakeholders",
        "impact": "Leads complex initiatives",
        "mentorship": "Coaches designers",
    }},
    {"level": "Staff", "expectations": {
        "product_strategy": "Drives multi-team strategy",
        "impact": "Org-level outcomes",
        "mentorship": "Grows design org",
    }},
    {"level": "Principal", "expectations": {
        "product_strategy": "Company-level strategy",
        "impact": "Industry influence",
        "mentorship": "Builds leaders",
    }},
]

@app.get("/api/reference")
def get_reference():
    return {"competencies": COMPETENCIES, "career_levels": CAREER_LEVELS}

# -------- Designers --------
class CreateDesigner(BaseModel):
    name: str
    email: str
    manager_id: Optional[str] = None
    current_level: str = "Junior"

@app.post("/api/designers")
def create_designer(payload: CreateDesigner):
    try:
        _id = create_document("designer", payload.model_dump())
        return {"id": _id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/designers")
def list_designers():
    try:
        items = get_documents("designer", {}, 200)
        for it in items:
            it["_id"] = str(it.get("_id"))
        return items
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# -------- Goals --------
class CreateGoal(BaseModel):
    designer_id: str
    title: str
    description: Optional[str] = None
    competency_key: Optional[str] = None
    target_date: Optional[str] = None  # ISO date

@app.post("/api/goals")
def create_goal(payload: CreateGoal):
    data = payload.model_dump()
    if data.get("target_date"):
        try:
            data["target_date"] = datetime.fromisoformat(data["target_date"])  # store as datetime
        except Exception:
            pass
    data.setdefault("status", "not_started")
    data.setdefault("progress", 0)
    try:
        _id = create_document("goal", data)
        return {"id": _id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/goals")
def list_goals(designer_id: Optional[str] = None):
    query: Dict[str, Any] = {}
    if designer_id:
        query["designer_id"] = designer_id
    try:
        items = get_documents("goal", query, 500)
        for it in items:
            it["_id"] = str(it.get("_id"))
        return items
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# -------- Skill Assessments --------
class CreateAssessment(BaseModel):
    designer_id: str
    cycle: str  # e.g., 2025-H1
    ratings: Dict[str, int]
    notes: Optional[str] = None

@app.post("/api/assessments")
def create_assessment(payload: CreateAssessment):
    data = payload.model_dump()
    for k, v in list(data.get("ratings", {}).items()):
        try:
            iv = int(v)
        except Exception:
            iv = 1
        data["ratings"][k] = max(1, min(4, iv))
    try:
        _id = create_document("skillassessment", data)
        return {"id": _id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/assessments")
def list_assessments(designer_id: str):
    try:
        items = get_documents("skillassessment", {"designer_id": designer_id}, 100)
        for it in items:
            it["_id"] = str(it.get("_id"))
        return items
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# -------- Performance Reviews --------
class CreateReview(BaseModel):
    designer_id: str
    cycle: str
    self_eval: Optional[Dict[str, int]] = None
    peer_evals: Optional[List[Dict[str, int]]] = None
    manager_eval: Optional[Dict[str, int]] = None
    summary: Optional[str] = None

@app.post("/api/reviews")
def create_review(payload: CreateReview):
    data = payload.model_dump()
    data.setdefault("status", "open")
    try:
        _id = create_document("review", data)
        return {"id": _id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/reviews")
def list_reviews(designer_id: Optional[str] = None, cycle: Optional[str] = None):
    query: Dict[str, Any] = {}
    if designer_id:
        query["designer_id"] = designer_id
    if cycle:
        query["cycle"] = cycle
    try:
        items = get_documents("review", query, 200)
        for it in items:
            it["_id"] = str(it.get("_id"))
        return items
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# -------- Guilds & Mentorship --------
class CreateGuild(BaseModel):
    name: str
    description: Optional[str] = None

@app.post("/api/guilds")
def create_guild(payload: CreateGuild):
    try:
        _id = create_document("guild", payload.model_dump())
        return {"id": _id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/guilds")
def list_guilds():
    try:
        items = get_documents("guild", {}, 200)
        for it in items:
            it["_id"] = str(it.get("_id"))
        return items
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

class CreateMentorship(BaseModel):
    mentor_id: str
    mentee_id: str
    status: Optional[str] = "active"

@app.post("/api/mentorships")
def create_mentorship(payload: CreateMentorship):
    data = payload.model_dump()
    data.setdefault("activities", [])
    try:
        _id = create_document("mentorship", data)
        return {"id": _id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/mentorships")
def list_mentorships(mentor_id: Optional[str] = None, mentee_id: Optional[str] = None):
    query: Dict[str, Any] = {}
    if mentor_id:
        query["mentor_id"] = mentor_id
    if mentee_id:
        query["mentee_id"] = mentee_id
    try:
        items = get_documents("mentorship", query, 200)
        for it in items:
            it["_id"] = str(it.get("_id"))
        return items
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# -------- Training Resources --------
class CreateResource(BaseModel):
    title: str
    url: str
    provider: Optional[str] = None
    tags: Optional[List[str]] = None

@app.post("/api/resources")
def create_resource(payload: CreateResource):
    data = payload.model_dump()
    data.setdefault("tags", [])
    try:
        _id = create_document("trainingresource", data)
        return {"id": _id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/resources")
def list_resources(tag: Optional[str] = None):
    query: Dict[str, Any] = {}
    if tag:
        query["tags"] = {"$in": [tag]}
    try:
        items = get_documents("trainingresource", query, 200)
        for it in items:
            it["_id"] = str(it.get("_id"))
        return items
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# -------- Projects --------
class CreateProject(BaseModel):
    name: str
    description: Optional[str] = None
    manager_id: Optional[str] = None
    designers: Optional[List[str]] = None

@app.post("/api/projects")
def create_project(payload: CreateProject):
    data = payload.model_dump()
    data.setdefault("designers", [])
    data.setdefault("stages", [])
    try:
        _id = create_document("project", data)
        return {"id": _id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/projects")
def list_projects(manager_id: Optional[str] = None, designer_id: Optional[str] = None):
    query: Dict[str, Any] = {}
    if manager_id:
        query["manager_id"] = manager_id
    if designer_id:
        query["designers"] = {"$in": [designer_id]}
    try:
        items = get_documents("project", query, 200)
        for it in items:
            it["_id"] = str(it.get("_id"))
        return items
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# -------- Notifications (log only) --------
class CreateNotification(BaseModel):
    user_id: str
    kind: str
    message: str
    sent_via: Optional[List[str]] = None

@app.post("/api/notifications")
def create_notification(payload: CreateNotification):
    data = payload.model_dump()
    data.setdefault("sent_via", [])
    try:
        _id = create_document("notification", data)
        return {"id": _id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/notifications")
def list_notifications(user_id: Optional[str] = None):
    query: Dict[str, Any] = {}
    if user_id:
        query["user_id"] = user_id
    try:
        items = get_documents("notification", query, 200)
        for it in items:
            it["_id"] = str(it.get("_id"))
        return items
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# -------- Dashboard summary --------
@app.get("/api/summary")
def summary(designer_id: Optional[str] = None):
    out: Dict[str, Any] = {"competencies": COMPETENCIES, "career_levels": CAREER_LEVELS}
    try:
        if designer_id:
            goals = get_documents("goal", {"designer_id": designer_id}, 100)
            asses = get_documents("skillassessment", {"designer_id": designer_id}, 10)
            reviews = get_documents("review", {"designer_id": designer_id}, 10)
            for coll in (goals, asses, reviews):
                for it in coll:
                    it["_id"] = str(it.get("_id"))
            out.update({"goals": goals, "assessments": asses, "reviews": reviews})
        return out
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
