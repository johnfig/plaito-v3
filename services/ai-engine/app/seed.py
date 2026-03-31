"""Seed the in-memory database with demo data for local testing."""

from datetime import datetime, timedelta, timezone

DEMO_USER_ID = "11111111-1111-1111-1111-111111111111"
DEMO_COURSE_ID = "22222222-2222-2222-2222-222222222222"

DEMO_CONCEPTS = [
    {"id": "c0000001-0000-0000-0000-000000000001", "name": "Derivatives", "weight": 1.0, "description": "Rate of change and slopes of curves"},
    {"id": "c0000002-0000-0000-0000-000000000002", "name": "Integrals", "weight": 1.0, "description": "Area under curves and accumulation"},
    {"id": "c0000003-0000-0000-0000-000000000003", "name": "Limits", "weight": 0.8, "description": "Behavior of functions as inputs approach a value"},
    {"id": "c0000004-0000-0000-0000-000000000004", "name": "Series & Sequences", "weight": 0.7, "description": "Infinite sums and convergence"},
    {"id": "c0000005-0000-0000-0000-000000000005", "name": "Differential Equations", "weight": 0.9, "description": "Equations involving derivatives"},
    {"id": "c0000006-0000-0000-0000-000000000006", "name": "Vectors", "weight": 0.5, "description": "Magnitude and direction in multi-dimensional space"},
]


def seed_database(db) -> None:
    """Populate the database with demo user, course, concepts, and mastery data."""
    now = datetime.now(timezone.utc)

    # User
    db.table("users").insert({
        "id": DEMO_USER_ID,
        "email": "demo@plaito.ai",
        "display_name": "Demo Student",
    }).execute()

    # Course
    db.table("courses").insert({
        "id": DEMO_COURSE_ID,
        "user_id": DEMO_USER_ID,
        "name": "Calculus II",
        "course_code": "MATH 201",
        "term": "Spring 2026",
        "target_grade": 90.0,
        "current_grade": None,
        "grading_scale": {
            "A": 90, "A-": 87, "B+": 83, "B": 80, "B-": 77,
            "C+": 73, "C": 70, "C-": 67, "D": 60, "F": 0,
        },
    }).execute()

    # Concepts
    for concept in DEMO_CONCEPTS:
        db.table("concepts").insert({
            **concept,
            "course_id": DEMO_COURSE_ID,
        }).execute()

    # Mastery scores — varying levels to make the demo interesting
    mastery_data = [
        # (concept_id, score, confidence, attempts, days_ago)
        ("c0000001-0000-0000-0000-000000000001", 0.88, 0.950, 12, 1),   # Derivatives: strong
        ("c0000002-0000-0000-0000-000000000002", 0.72, 0.777, 5, 3),    # Integrals: decent
        ("c0000003-0000-0000-0000-000000000003", 0.55, 0.593, 3, 7),    # Limits: weak, stale
        ("c0000004-0000-0000-0000-000000000004", 0.30, 0.451, 2, 14),   # Series: struggling
        ("c0000005-0000-0000-0000-000000000005", 0.45, 0.259, 1, 2),    # DiffEq: just started
        # Vectors: no mastery data yet (never practiced)
    ]

    for concept_id, score, confidence, attempts, days_ago in mastery_data:
        last_practiced = (now - timedelta(days=days_ago)).isoformat()
        db.table("mastery_scores").insert({
            "user_id": DEMO_USER_ID,
            "concept_id": concept_id,
            "score": score,
            "confidence": confidence,
            "attempt_count": attempts,
            "last_practiced_at": last_practiced,
        }).execute()

    # A few historical grade snapshots for trend detection
    for i, grade in enumerate([68.5, 70.2, 72.1]):
        db.table("grade_snapshots").insert({
            "user_id": DEMO_USER_ID,
            "course_id": DEMO_COURSE_ID,
            "predicted_grade": grade,
            "predicted_letter": "C-" if grade < 70 else "C",
            "confidence": 0.5 + i * 0.05,
            "factors": [],
            "snapshot_type": "auto",
            "created_at": (now - timedelta(days=7 - i * 2)).isoformat(),
        }).execute()
