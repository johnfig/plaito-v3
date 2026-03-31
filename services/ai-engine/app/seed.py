"""Seed the in-memory database with demo data for local testing."""

from datetime import datetime, timedelta, timezone

DEMO_USER_ID = "11111111-1111-1111-1111-111111111111"

COURSES = [
    {
        "id": "22222222-2222-2222-2222-222222222222",
        "name": "Calculus II",
        "course_code": "MATH 201",
        "emoji": "📐",
        "target_grade": 90.0,
        "concepts": [
            {"id": "c0000001-0000-0000-0000-000000000001", "name": "Derivatives", "weight": 1.0, "description": "Rate of change and slopes of curves"},
            {"id": "c0000002-0000-0000-0000-000000000002", "name": "Integrals", "weight": 1.0, "description": "Area under curves and accumulation"},
            {"id": "c0000003-0000-0000-0000-000000000003", "name": "Limits", "weight": 0.8, "description": "Behavior of functions as inputs approach a value"},
            {"id": "c0000004-0000-0000-0000-000000000004", "name": "Series & Sequences", "weight": 0.7, "description": "Infinite sums and convergence"},
            {"id": "c0000005-0000-0000-0000-000000000005", "name": "Differential Equations", "weight": 0.9, "description": "Equations involving derivatives"},
            {"id": "c0000006-0000-0000-0000-000000000006", "name": "Vectors", "weight": 0.5, "description": "Magnitude and direction in multi-dimensional space"},
        ],
        "mastery": [
            ("c0000001-0000-0000-0000-000000000001", 0.88, 0.950, 12, 1),
            ("c0000002-0000-0000-0000-000000000002", 0.72, 0.777, 5, 3),
            ("c0000003-0000-0000-0000-000000000003", 0.55, 0.593, 3, 7),
            ("c0000004-0000-0000-0000-000000000004", 0.30, 0.451, 2, 14),
            ("c0000005-0000-0000-0000-000000000005", 0.45, 0.259, 1, 2),
        ],
        "snapshots": [68.5, 70.2, 72.1],
    },
    {
        "id": "33333333-3333-3333-3333-333333333333",
        "name": "AP Chemistry",
        "course_code": "CHEM 150",
        "emoji": "🧪",
        "target_grade": 85.0,
        "concepts": [
            {"id": "c1000001-0000-0000-0000-000000000001", "name": "Stoichiometry", "weight": 1.0, "description": "Quantitative relationships in chemical reactions"},
            {"id": "c1000002-0000-0000-0000-000000000002", "name": "Thermodynamics", "weight": 0.9, "description": "Energy changes in chemical processes"},
            {"id": "c1000003-0000-0000-0000-000000000003", "name": "Equilibrium", "weight": 0.8, "description": "Balance in reversible reactions"},
            {"id": "c1000004-0000-0000-0000-000000000004", "name": "Acid-Base Chemistry", "weight": 0.8, "description": "Proton transfer reactions and pH"},
            {"id": "c1000005-0000-0000-0000-000000000005", "name": "Atomic Structure", "weight": 0.7, "description": "Electron configuration and periodicity"},
        ],
        "mastery": [
            ("c1000001-0000-0000-0000-000000000001", 0.82, 0.900, 8, 2),
            ("c1000002-0000-0000-0000-000000000002", 0.65, 0.700, 4, 5),
            ("c1000003-0000-0000-0000-000000000003", 0.40, 0.451, 2, 10),
            ("c1000004-0000-0000-0000-000000000004", 0.75, 0.777, 5, 1),
        ],
        "snapshots": [72.0, 74.5, 76.8],
    },
    {
        "id": "44444444-4444-4444-4444-444444444444",
        "name": "AP US History",
        "course_code": "HIST 101",
        "emoji": "📜",
        "target_grade": 88.0,
        "concepts": [
            {"id": "c2000001-0000-0000-0000-000000000001", "name": "Colonial Period", "weight": 0.7, "description": "European settlement and colonial society"},
            {"id": "c2000002-0000-0000-0000-000000000002", "name": "American Revolution", "weight": 0.8, "description": "Independence movement and founding principles"},
            {"id": "c2000003-0000-0000-0000-000000000003", "name": "Civil War & Reconstruction", "weight": 0.9, "description": "National conflict and reunification"},
            {"id": "c2000004-0000-0000-0000-000000000004", "name": "Industrialization", "weight": 0.8, "description": "Economic transformation and labor movements"},
            {"id": "c2000005-0000-0000-0000-000000000005", "name": "World Wars", "weight": 1.0, "description": "America's role in global conflicts"},
            {"id": "c2000006-0000-0000-0000-000000000006", "name": "Civil Rights Movement", "weight": 0.9, "description": "Struggle for equality and justice"},
        ],
        "mastery": [
            ("c2000001-0000-0000-0000-000000000001", 0.91, 0.970, 15, 1),
            ("c2000002-0000-0000-0000-000000000002", 0.85, 0.900, 9, 2),
            ("c2000003-0000-0000-0000-000000000003", 0.78, 0.830, 6, 3),
            ("c2000004-0000-0000-0000-000000000004", 0.60, 0.700, 4, 8),
            ("c2000005-0000-0000-0000-000000000005", 0.35, 0.451, 2, 12),
        ],
        "snapshots": [78.0, 80.5, 82.3],
    },
]

GRADING_SCALE = {
    "A": 90, "A-": 87, "B+": 83, "B": 80, "B-": 77,
    "C+": 73, "C": 70, "C-": 67, "D": 60, "F": 0,
}


def seed_database(db) -> None:
    """Populate the database with demo user, courses, concepts, and mastery data."""
    now = datetime.now(timezone.utc)

    # User
    db.table("users").insert({
        "id": DEMO_USER_ID,
        "email": "demo@plaito.ai",
        "display_name": "Alex",
        "school_name": "Lincoln High School",
        "grade_level": "Junior",
    }).execute()

    for course in COURSES:
        # Course
        db.table("courses").insert({
            "id": course["id"],
            "user_id": DEMO_USER_ID,
            "name": course["name"],
            "course_code": course["course_code"],
            "emoji": course.get("emoji", "📚"),
            "term": "Spring 2026",
            "target_grade": course["target_grade"],
            "current_grade": None,
            "is_active": True,
            "grading_scale": GRADING_SCALE,
        }).execute()

        # Concepts
        for concept in course["concepts"]:
            db.table("concepts").insert({
                **concept,
                "course_id": course["id"],
            }).execute()

        # Mastery scores
        for concept_id, score, confidence, attempts, days_ago in course["mastery"]:
            last_practiced = (now - timedelta(days=days_ago)).isoformat()
            db.table("mastery_scores").insert({
                "user_id": DEMO_USER_ID,
                "concept_id": concept_id,
                "score": score,
                "confidence": confidence,
                "attempt_count": attempts,
                "last_practiced_at": last_practiced,
            }).execute()

        # Historical grade snapshots
        for i, grade in enumerate(course["snapshots"]):
            db.table("grade_snapshots").insert({
                "user_id": DEMO_USER_ID,
                "course_id": course["id"],
                "predicted_grade": grade,
                "predicted_letter": "C" if grade < 80 else "B",
                "confidence": 0.5 + i * 0.05,
                "factors": [],
                "snapshot_type": "auto",
                "created_at": (now - timedelta(days=7 - i * 2)).isoformat(),
            }).execute()
