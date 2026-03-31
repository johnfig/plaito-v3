"""Tests for the grade prediction engine."""

from unittest.mock import MagicMock
from uuid import uuid4

from app.engines.grade_predictor import GradePredictor
from tests.conftest import (
    COURSE_ID,
    USER_ID,
    MockSupabaseClient,
    make_concepts,
    make_mastery_scores,
)


def _setup_db(
    scores=None, days_ago=None, attempts=None, snapshots=None, course=None
) -> MockSupabaseClient:
    db = MockSupabaseClient()
    db.set_table_data("concepts", make_concepts())
    db.set_table_data(
        "mastery_scores",
        make_mastery_scores(scores=scores, days_ago=days_ago, attempts=attempts),
    )
    db.set_table_data("grade_snapshots", snapshots or [])
    db.set_table_data("courses", [course] if course else [{
        "id": COURSE_ID,
        "grading_scale": {
            "A": 90, "A-": 87, "B+": 83, "B": 80, "B-": 77,
            "C+": 73, "C": 70, "C-": 67, "D": 60, "F": 0,
        },
        "target_grade": 90.0,
    }])
    return db


class TestPrediction:
    def test_high_mastery_predicts_high_grade(self):
        db = _setup_db(
            scores=[0.95, 0.92, 0.88, 0.90, 0.85],
            days_ago=[0, 0, 0, 0, 0],
            attempts=[10, 10, 10, 10, 10],
        )
        predictor = GradePredictor(db)
        prediction = predictor.predict(USER_ID, COURSE_ID)

        assert prediction.predicted_grade > 80
        assert prediction.confidence > 0.5

    def test_low_mastery_predicts_low_grade(self):
        db = _setup_db(
            scores=[0.2, 0.15, 0.1, 0.05, 0.1],
            days_ago=[0, 0, 0, 0, 0],
            attempts=[10, 10, 10, 10, 10],
        )
        predictor = GradePredictor(db)
        prediction = predictor.predict(USER_ID, COURSE_ID)

        assert prediction.predicted_grade < 30

    def test_no_concepts_returns_empty_prediction(self):
        db = MockSupabaseClient()
        db.set_table_data("concepts", [])
        db.set_table_data("mastery_scores", [])
        db.set_table_data("grade_snapshots", [])
        db.set_table_data("courses", [])

        predictor = GradePredictor(db)
        prediction = predictor.predict(USER_ID, COURSE_ID)

        assert prediction.predicted_grade == 0.0
        assert prediction.predicted_letter == "N/A"
        assert prediction.trend == "new"

    def test_no_mastery_data_returns_low_confidence(self):
        db = _setup_db(attempts=[0, 0, 0, 0, 0])
        predictor = GradePredictor(db)
        prediction = predictor.predict(USER_ID, COURSE_ID)

        assert prediction.confidence == 0.0

    def test_mixed_mastery(self):
        db = _setup_db(
            scores=[0.9, 0.7, 0.5, 0.3, 0.0],
            days_ago=[1, 3, 7, 14, 0],
            attempts=[10, 5, 3, 2, 0],
        )
        predictor = GradePredictor(db)
        prediction = predictor.predict(USER_ID, COURSE_ID)

        # Should be somewhere in the middle
        assert 30 < prediction.predicted_grade < 90


class TestLetterGrade:
    def test_a_grade(self):
        assert GradePredictor._grade_to_letter(95, {"A": 90, "B": 80, "F": 0}) == "A"

    def test_b_grade(self):
        assert GradePredictor._grade_to_letter(85, {"A": 90, "B": 80, "F": 0}) == "B"

    def test_f_grade(self):
        assert GradePredictor._grade_to_letter(50, {"A": 90, "B": 80, "F": 0}) == "F"

    def test_boundary(self):
        assert GradePredictor._grade_to_letter(90, {"A": 90, "B": 80, "F": 0}) == "A"


class TestRecommendations:
    def test_generates_recommendations_for_gaps(self):
        mastery_map = [
            {"concept_name": "Derivatives", "effective_score": 0.3, "weight": 1.0, "days_since_practice": 2},
            {"concept_name": "Integrals", "effective_score": 0.9, "weight": 1.0, "days_since_practice": 1},
        ]
        actions = GradePredictor._build_recommendations(mastery_map)
        assert any("Derivatives" in a for a in actions)

    def test_stale_concepts_get_review_warning(self):
        mastery_map = [
            {"concept_name": "Limits", "effective_score": 0.5, "weight": 0.8, "days_since_practice": 15},
        ]
        actions = GradePredictor._build_recommendations(mastery_map)
        assert any("15 days ago" in a for a in actions)

    def test_all_mastered_gets_encouragement(self):
        mastery_map = [
            {"concept_name": "X", "effective_score": 0.95, "weight": 1.0, "days_since_practice": 1},
        ]
        actions = GradePredictor._build_recommendations(mastery_map)
        assert any("on track" in a for a in actions)


class TestSessionEstimate:
    def test_at_target(self):
        assert GradePredictor._estimate_sessions_to_target(90, 90) == 0

    def test_above_target(self):
        assert GradePredictor._estimate_sessions_to_target(95, 90) == 0

    def test_below_target(self):
        sessions = GradePredictor._estimate_sessions_to_target(75, 90)
        assert sessions == 5  # (90-75) / 3.0 = 5


class TestTrend:
    def test_new_trend_with_no_history(self):
        db = _setup_db(snapshots=[])
        predictor = GradePredictor(db)
        trend = predictor._calculate_trend(USER_ID, COURSE_ID, 80)
        assert trend == "new"

    def test_improving_trend(self):
        snapshots = [
            {"predicted_grade": 70, "snapshot_type": "auto"},
            {"predicted_grade": 68, "snapshot_type": "auto"},
            {"predicted_grade": 65, "snapshot_type": "auto"},
        ]
        db = _setup_db(snapshots=snapshots)
        predictor = GradePredictor(db)
        trend = predictor._calculate_trend(USER_ID, COURSE_ID, 80)
        assert trend == "improving"

    def test_declining_trend(self):
        snapshots = [
            {"predicted_grade": 90, "snapshot_type": "auto"},
            {"predicted_grade": 92, "snapshot_type": "auto"},
            {"predicted_grade": 88, "snapshot_type": "auto"},
        ]
        db = _setup_db(snapshots=snapshots)
        predictor = GradePredictor(db)
        trend = predictor._calculate_trend(USER_ID, COURSE_ID, 75)
        assert trend == "declining"

    def test_stable_trend(self):
        snapshots = [
            {"predicted_grade": 80, "snapshot_type": "auto"},
            {"predicted_grade": 79, "snapshot_type": "auto"},
            {"predicted_grade": 81, "snapshot_type": "auto"},
        ]
        db = _setup_db(snapshots=snapshots)
        predictor = GradePredictor(db)
        trend = predictor._calculate_trend(USER_ID, COURSE_ID, 80)
        assert trend == "stable"
