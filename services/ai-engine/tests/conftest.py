"""Test fixtures — mock Supabase client and sample data."""

from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock
from uuid import uuid4

import pytest


# ---------------------------------------------------------------------------
# Sample IDs
# ---------------------------------------------------------------------------

USER_ID = str(uuid4())
COURSE_ID = str(uuid4())
CONCEPT_IDS = [str(uuid4()) for _ in range(5)]


# ---------------------------------------------------------------------------
# Sample data builders
# ---------------------------------------------------------------------------

def make_concepts(course_id: str = COURSE_ID) -> list[dict]:
    names = ["Derivatives", "Integrals", "Limits", "Series", "Vectors"]
    weights = [1.0, 1.0, 0.8, 0.7, 0.5]
    return [
        {
            "id": CONCEPT_IDS[i],
            "course_id": course_id,
            "name": names[i],
            "description": f"Test concept: {names[i]}",
            "weight": weights[i],
            "parent_concept_id": None,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        for i in range(5)
    ]


def make_mastery_scores(
    user_id: str = USER_ID,
    scores: list[float] | None = None,
    days_ago: list[int] | None = None,
    attempts: list[int] | None = None,
) -> list[dict]:
    scores = scores or [0.9, 0.7, 0.5, 0.3, 0.0]
    days_ago = days_ago or [1, 3, 7, 14, 0]
    attempts = attempts or [10, 5, 3, 2, 0]

    results = []
    for i in range(5):
        if attempts[i] == 0:
            continue  # No mastery data for this concept
        now = datetime.now(timezone.utc)
        last_practiced = (now - timedelta(days=days_ago[i])).isoformat()
        results.append({
            "id": str(uuid4()),
            "user_id": user_id,
            "concept_id": CONCEPT_IDS[i],
            "score": scores[i],
            "confidence": min(1.0, 1.0 - __import__("math").exp(-0.3 * attempts[i])),
            "attempt_count": attempts[i],
            "last_practiced_at": last_practiced,
            "created_at": now.isoformat(),
            "updated_at": now.isoformat(),
        })
    return results


def make_course(course_id: str = COURSE_ID, user_id: str = USER_ID) -> dict:
    return {
        "id": course_id,
        "user_id": user_id,
        "name": "Calculus II",
        "course_code": "MATH 201",
        "term": "Spring 2026",
        "current_grade": None,
        "target_grade": 90.0,
        "grading_scale": {
            "A": 90, "A-": 87, "B+": 83, "B": 80, "B-": 77,
            "C+": 73, "C": 70, "C-": 67, "D": 60, "F": 0,
        },
        "is_active": True,
    }


# ---------------------------------------------------------------------------
# Mock Supabase client
# ---------------------------------------------------------------------------

class MockQueryBuilder:
    """Chainable mock that simulates Supabase query builder."""

    def __init__(self, data=None):
        self._data = data or []

    def select(self, *args, **kwargs):
        return self

    def insert(self, data):
        if isinstance(data, dict):
            data = {**data, "id": str(uuid4())}
            self._data = [data]
        return self

    def update(self, data):
        return self

    def eq(self, col, val):
        return self

    def neq(self, col, val):
        return self

    def order(self, col, **kwargs):
        return self

    def limit(self, n):
        self._data = self._data[:n]
        return self

    def range(self, start, end):
        self._data = self._data[start:end + 1]
        return self

    def execute(self):
        return MagicMock(data=self._data)

    def maybe_single(self):
        return MockQueryBuilder(self._data[0] if self._data else None)


class MockSupabaseClient:
    """Mock Supabase client for testing."""

    def __init__(self):
        self._tables: dict[str, list[dict]] = {}

    def set_table_data(self, table_name: str, data: list[dict]):
        self._tables[table_name] = data

    def table(self, name: str) -> MockQueryBuilder:
        data = self._tables.get(name, [])
        return MockQueryBuilder(data)


@pytest.fixture
def mock_db():
    return MockSupabaseClient()


@pytest.fixture
def sample_concepts():
    return make_concepts()


@pytest.fixture
def sample_mastery():
    return make_mastery_scores()


@pytest.fixture
def sample_course():
    return make_course()
