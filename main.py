from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from pydantic import BaseModel
from typing import List, Optional
from datetime import date, datetime
import uuid
import uvicorn
import os

app = FastAPI(title="Gym Workout Tracker API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── In-memory DB ──────────────────────────────────────────
workouts_db: List[dict] = []

# ── Schemas ───────────────────────────────────────────────

class WorkoutCreate(BaseModel):
    name: str
    category: str
    reps: Optional[int]        = None
    sets: Optional[int]        = None
    weight_kg: Optional[float] = None
    duration_mins: Optional[int] = None
    notes: Optional[str]       = None
    workout_date: Optional[str] = None

class WorkoutUpdate(BaseModel):
    name: Optional[str]          = None
    category: Optional[str]      = None
    reps: Optional[int]          = None
    sets: Optional[int]          = None
    weight_kg: Optional[float]   = None
    duration_mins: Optional[int] = None
    notes: Optional[str]         = None
    workout_date: Optional[str]  = None

class Workout(BaseModel):
    id: str
    name: str
    category: str
    reps: Optional[int]
    sets: Optional[int]
    weight_kg: Optional[float]
    duration_mins: Optional[int]
    notes: Optional[str]
    workout_date: str
    created_at: str

# ── Routes ────────────────────────────────────────────────

@app.get("/", response_class=HTMLResponse)
def serve_ui():
    # Read index.html from same folder as main.py
    html_path = os.path.join(os.path.dirname(__file__), "index.html")
    with open(html_path, "r", encoding="utf-8") as f:
        return f.read()

# GET all workouts — optional ?date= and ?category= filters
@app.get("/api/workouts", response_model=List[Workout])
def get_workouts(date: Optional[str] = None, category: Optional[str] = None):
    result = workouts_db
    if date:
        result = [w for w in result if w["workout_date"] == date]
    if category:
        result = [w for w in result if w["category"].lower() == category.lower()]
    return result

# GET single workout by ID
@app.get("/api/workouts/{workout_id}", response_model=Workout)
def get_workout(workout_id: str):
    for w in workouts_db:
        if w["id"] == workout_id:
            return w
    raise HTTPException(status_code=404, detail="Workout not found")

# POST — log a new workout
@app.post("/api/workouts", response_model=Workout, status_code=201)
def create_workout(payload: WorkoutCreate):
    if not payload.name.strip():
        raise HTTPException(status_code=400, detail="name cannot be empty")
    if not payload.category.strip():
        raise HTTPException(status_code=400, detail="category cannot be empty")

    workout = {
        "id":            str(uuid.uuid4()),
        "name":          payload.name.strip(),
        "category":      payload.category.lower().strip(),
        "reps":          payload.reps,
        "sets":          payload.sets,
        "weight_kg":     payload.weight_kg,
        "duration_mins": payload.duration_mins,
        "notes":         payload.notes,
        "workout_date":  payload.workout_date or date.today().isoformat(),
        "created_at":    datetime.utcnow().isoformat(),
    }
    workouts_db.append(workout)
    return workout

# PUT — update a workout
@app.put("/api/workouts/{workout_id}", response_model=Workout)
def update_workout(workout_id: str, payload: WorkoutUpdate):
    for w in workouts_db:
        if w["id"] == workout_id:
            if payload.name          is not None: w["name"]          = payload.name.strip()
            if payload.category      is not None: w["category"]      = payload.category.lower().strip()
            if payload.reps          is not None: w["reps"]          = payload.reps
            if payload.sets          is not None: w["sets"]          = payload.sets
            if payload.weight_kg     is not None: w["weight_kg"]     = payload.weight_kg
            if payload.duration_mins is not None: w["duration_mins"] = payload.duration_mins
            if payload.notes         is not None: w["notes"]         = payload.notes
            if payload.workout_date  is not None: w["workout_date"]  = payload.workout_date
            return w
    raise HTTPException(status_code=404, detail="Workout not found")

# DELETE — remove a workout
@app.delete("/api/workouts/{workout_id}", status_code=204)
def delete_workout(workout_id: str):
    for i, w in enumerate(workouts_db):
        if w["id"] == workout_id:
            workouts_db.pop(i)
            return
    raise HTTPException(status_code=404, detail="Workout not found")

# DELETE all — reset for tests
@app.delete("/api/workouts", status_code=204)
def reset_workouts():
    workouts_db.clear()

# GET summary
@app.get("/api/summary")
def get_summary(date: Optional[str] = None):
    target = date or datetime.today().strftime("%Y-%m-%d")
    day_workouts = [w for w in workouts_db if w["workout_date"] == target]
    by_category = {}
    for w in day_workouts:
        by_category[w["category"]] = by_category.get(w["category"], 0) + 1
    return {
        "date":            target,
        "total_workouts":  len(day_workouts),
        "by_category":     by_category,
        "total_volume_kg": round(sum(
            (w["sets"] or 1) * (w["reps"] or 1) * (w["weight_kg"] or 0)
            for w in day_workouts
        ), 2),
    }

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True,
                reload_excludes=[".venv"])