"""
demo.py — Seeds the Gym Tracker API with realistic workout data.

Usage:
    python demo.py

Make sure the server is running first:
    uvicorn app.main:app --reload --port 8000
"""

import requests
from datetime import date, timedelta

BASE = "http://localhost:8000/api/workouts"

def post(payload):
    res = requests.post(BASE, json=payload)
    if res.status_code == 201:
        w = res.json()
        print(f"  ✓  [{w['category'].upper():10}]  {w['name']:<25} {w['workout_date']}")
    else:
        print(f"  ✗  Failed: {res.text}")

today     = date.today().isoformat()
yesterday = (date.today() - timedelta(days=1)).isoformat()
two_days  = (date.today() - timedelta(days=2)).isoformat()

print("\n🏋️  Seeding Gym Tracker with demo workouts...\n")

# ── Today — Push day ──────────────────────────────────────
print("📅 Today (Push Day):")
post({"name": "Bench Press",        "category": "chest",     "sets": 4, "reps": 10, "weight_kg": 80.0,  "notes": "New PR on last set!", "workout_date": today})
post({"name": "Incline Dumbbell Press","category": "chest",  "sets": 3, "reps": 12, "weight_kg": 28.0,  "workout_date": today})
post({"name": "Overhead Press",     "category": "shoulders", "sets": 4, "reps": 8,  "weight_kg": 50.0,  "workout_date": today})
post({"name": "Lateral Raises",     "category": "shoulders", "sets": 3, "reps": 15, "weight_kg": 10.0,  "workout_date": today})
post({"name": "Tricep Pushdown",    "category": "arms",      "sets": 3, "reps": 12, "weight_kg": 25.0,  "workout_date": today})

# ── Yesterday — Pull day ──────────────────────────────────
print("\n📅 Yesterday (Pull Day):")
post({"name": "Deadlift",           "category": "back",      "sets": 5, "reps": 5,  "weight_kg": 120.0, "notes": "Felt heavy, good form", "workout_date": yesterday})
post({"name": "Pull Ups",           "category": "back",      "sets": 4, "reps": 8,  "workout_date": yesterday})
post({"name": "Barbell Row",        "category": "back",      "sets": 4, "reps": 10, "weight_kg": 70.0,  "workout_date": yesterday})
post({"name": "Bicep Curl",         "category": "arms",      "sets": 3, "reps": 12, "weight_kg": 15.0,  "workout_date": yesterday})
post({"name": "Face Pulls",         "category": "shoulders", "sets": 3, "reps": 15, "weight_kg": 20.0,  "workout_date": yesterday})

# ── Two days ago — Leg day ────────────────────────────────
print("\n📅 Two days ago (Leg Day):")
post({"name": "Squat",              "category": "legs",      "sets": 5, "reps": 5,  "weight_kg": 100.0, "notes": "Legs on fire", "workout_date": two_days})
post({"name": "Romanian Deadlift",  "category": "legs",      "sets": 4, "reps": 10, "weight_kg": 80.0,  "workout_date": two_days})
post({"name": "Leg Press",          "category": "legs",      "sets": 4, "reps": 12, "weight_kg": 150.0, "workout_date": two_days})
post({"name": "Calf Raises",        "category": "legs",      "sets": 4, "reps": 20, "weight_kg": 60.0,  "workout_date": two_days})
post({"name": "Treadmill Run",      "category": "cardio",    "duration_mins": 20,                       "workout_date": two_days})
post({"name": "Plank",              "category": "core",      "sets": 3, "duration_mins": 1,             "workout_date": two_days})

# ── Summary ───────────────────────────────────────────────
print("\n📊 Fetching today's summary...")
summary = requests.get(f"http://localhost:8000/api/summary?date={today}").json()
print(f"\n  Date           : {summary['date']}")
print(f"  Total workouts : {summary['total_workouts']}")
print(f"  Total volume   : {summary['total_volume_kg']} kg")
print(f"  By category    : {summary['by_category']}")

total = requests.get("http://localhost:8000/api/workouts")
print(f"\n  Total workouts seeded: {len(total.json())}")
print("\n✅  Done! Open http://localhost:8000 to see your workouts.\n")
