"""Grade prediction engine — V1 heuristic weighted model."""

from __future__ import annotations

from math import ceil
from typing import TYPE_CHECKING, Any

from app.engines.knowledge_graph import KnowledgeGraphProcessor
from app.models.schemas import GradeFactor, GradePrediction

if TYPE_CHECKING:
    from supabase import Client


# Average grade-point improvement per 10-minute tutoring session.
# Calibrated over time from real data.
AVG_IMPROVEMENT_PER_SESSION = 3.0

# Default grading scale (can be overridden per course)
DEFAULT_GRADING_SCALE = {
    "A": 90, "A-": 87, "B+": 83, "B": 80, "B-": 77,
    "C+": 73, "C": 70, "C-": 67, "D": 60, "F": 0,
}


class GradePredictor:
    def __init__(self, db: Any):
        self.db = db
        self.kg = KnowledgeGraphProcessor(db)

    def predict(self, user_id: str, course_id: str) -> GradePrediction:
        """Run the V1 grade prediction algorithm."""
        # 1. Get mastery map (concepts + decay-adjusted scores)
        mastery_map = self.kg.get_mastery_map(user_id, course_id)

        if not mastery_map:
            return GradePrediction(
                predicted_grade=0.0,
                predicted_letter="N/A",
                confidence=0.0,
                factors=[],
                recommended_actions=["Add concepts to this course to start predictions."],
                trend="new",
            )

        # 2. Weighted average of effective mastery (only scored concepts)
        weighted_sum = 0.0
        active_weight = 0.0
        total_concepts = len(mastery_map)
        scored_concepts = 0

        for c in mastery_map:
            if c["confidence"] > 0:
                weight_contribution = c["weight"] * c["confidence"]
                weighted_sum += c["effective_score"] * weight_contribution
                active_weight += weight_contribution
                scored_concepts += 1

        if active_weight == 0:
            raw_prediction = 50.0  # Not enough data, assume average
            prediction_confidence = 0.0
        else:
            raw_prediction = (weighted_sum / active_weight) * 100
            # Confidence: coverage * average mastery confidence
            coverage = scored_concepts / total_concepts
            avg_confidence = sum(
                c["confidence"] for c in mastery_map if c["confidence"] > 0
            ) / max(scored_concepts, 1)
            prediction_confidence = round(coverage * avg_confidence, 3)

        # 3. Apply calibration offset from reported actual grades
        calibration = self._get_calibration_offset(user_id, course_id)
        calibrated_prediction = max(0, min(100, raw_prediction - calibration))

        # 4. Get course grading scale
        course = (
            self.db.table("courses")
            .select("grading_scale, target_grade")
            .eq("id", course_id)
            .maybe_single()
            .execute()
        )
        grading_scale = DEFAULT_GRADING_SCALE
        target_grade = 90.0
        if course.data:
            if course.data.get("grading_scale"):
                grading_scale = course.data["grading_scale"]
            if course.data.get("target_grade"):
                target_grade = float(course.data["target_grade"])

        # 5. Map to letter grade
        predicted_letter = self._grade_to_letter(calibrated_prediction, grading_scale)

        # 6. Build factors list (sorted by impact)
        factors = self._build_factors(mastery_map)

        # 7. Generate recommended actions
        recommended_actions = self._build_recommendations(mastery_map)

        # 8. Estimate sessions to target
        sessions_to_target = self._estimate_sessions_to_target(
            calibrated_prediction, target_grade
        )

        # 9. Determine trend
        trend = self._calculate_trend(user_id, course_id, calibrated_prediction)

        return GradePrediction(
            predicted_grade=round(calibrated_prediction, 1),
            predicted_letter=predicted_letter,
            confidence=prediction_confidence,
            factors=factors,
            recommended_actions=recommended_actions,
            sessions_to_target=sessions_to_target,
            trend=trend,
        )

    def save_snapshot(
        self,
        user_id: str,
        course_id: str,
        prediction: GradePrediction,
        snapshot_type: str = "auto",
    ) -> str | None:
        """Save a grade prediction snapshot. Returns snapshot ID."""
        result = self.db.table("grade_snapshots").insert({
            "user_id": user_id,
            "course_id": course_id,
            "predicted_grade": prediction.predicted_grade,
            "predicted_letter": prediction.predicted_letter,
            "confidence": prediction.confidence,
            "factors": [f.model_dump() for f in prediction.factors],
            "snapshot_type": snapshot_type,
        }).execute()

        if result.data:
            return result.data[0]["id"]
        return None

    def get_history(
        self, user_id: str, course_id: str, limit: int = 30, offset: int = 0
    ) -> list[dict]:
        """Fetch grade prediction snapshots for the timeline chart."""
        result = (
            self.db.table("grade_snapshots")
            .select("id, predicted_grade, predicted_letter, confidence, snapshot_type, created_at")
            .eq("user_id", user_id)
            .eq("course_id", course_id)
            .order("created_at", desc=True)
            .range(offset, offset + limit - 1)
            .execute()
        )
        return result.data or []

    def report_actual_grade(
        self, user_id: str, course_id: str, actual_grade: float
    ) -> dict:
        """Record an actual grade and compute calibration offset."""
        # Update the course's current grade
        self.db.table("courses").update({
            "current_grade": actual_grade,
        }).eq("id", course_id).execute()

        # Get the most recent prediction to compute offset
        latest = (
            self.db.table("grade_snapshots")
            .select("predicted_grade")
            .eq("user_id", user_id)
            .eq("course_id", course_id)
            .order("created_at", desc=True)
            .limit(1)
            .execute()
        )

        offset_value = 0.0
        if latest.data:
            offset_value = float(latest.data[0]["predicted_grade"]) - actual_grade

        # Save a calibration snapshot
        self.db.table("grade_snapshots").insert({
            "user_id": user_id,
            "course_id": course_id,
            "predicted_grade": actual_grade,
            "predicted_letter": self._grade_to_letter(actual_grade, DEFAULT_GRADING_SCALE),
            "confidence": 1.0,
            "factors": [],
            "calibration_offset": round(offset_value, 2),
            "snapshot_type": "calibration",
        }).execute()

        return {
            "actual_grade": actual_grade,
            "calibration_offset": round(offset_value, 2),
        }

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _get_calibration_offset(self, user_id: str, course_id: str) -> float:
        """Get average calibration offset from past reported grades."""
        result = (
            self.db.table("grade_snapshots")
            .select("calibration_offset")
            .eq("user_id", user_id)
            .eq("course_id", course_id)
            .eq("snapshot_type", "calibration")
            .execute()
        )
        if not result.data:
            return 0.0

        offsets = [float(r["calibration_offset"]) for r in result.data if r["calibration_offset"]]
        return sum(offsets) / len(offsets) if offsets else 0.0

    @staticmethod
    def _grade_to_letter(grade: float, grading_scale: dict) -> str:
        """Map a numeric grade to a letter using the grading scale."""
        sorted_grades = sorted(
            grading_scale.items(), key=lambda x: x[1], reverse=True
        )
        for letter, threshold in sorted_grades:
            if grade >= threshold:
                return letter
        return "F"

    @staticmethod
    def _build_factors(mastery_map: list[dict]) -> list[GradeFactor]:
        """Build per-concept impact factors, sorted by impact descending."""
        factors = []
        for c in mastery_map:
            impact = c["weight"] * (1.0 - c["effective_score"])
            factors.append(GradeFactor(
                concept_name=c["concept_name"],
                concept_id=c["concept_id"],
                weight=c["weight"],
                effective_mastery=round(c["effective_score"] * 100, 1),
                impact=round(impact, 3),
                days_since_practice=c["days_since_practice"],
            ))
        factors.sort(key=lambda f: f.impact, reverse=True)
        return factors

    @staticmethod
    def _build_recommendations(mastery_map: list[dict]) -> list[str]:
        """Generate top 3 actionable recommendations from gaps."""
        gaps = [
            c for c in mastery_map
            if c["effective_score"] < 0.7
        ]
        gaps.sort(
            key=lambda c: c["weight"] * (0.7 - c["effective_score"]),
            reverse=True,
        )

        actions = []
        for gap in gaps[:3]:
            pct = round(gap["effective_score"] * 100)
            actions.append(
                f"Practice '{gap['concept_name']}' — currently at {pct}% mastery"
            )

        # Add decay warning
        stale = [
            c for c in mastery_map
            if c["days_since_practice"] is not None and c["days_since_practice"] > 7
            and c["effective_score"] > 0
        ]
        stale.sort(key=lambda c: c["days_since_practice"] or 0, reverse=True)
        for s in stale[:1]:
            actions.append(
                f"Review '{s['concept_name']}' — last practiced {s['days_since_practice']} days ago"
            )

        if not actions:
            actions.append("You're on track! Keep your streak going.")

        return actions

    @staticmethod
    def _estimate_sessions_to_target(
        current: float, target: float
    ) -> int | None:
        """Estimate tutoring sessions needed to reach target grade."""
        gap = target - current
        if gap <= 0:
            return 0
        return ceil(gap / AVG_IMPROVEMENT_PER_SESSION)

    def _calculate_trend(
        self, user_id: str, course_id: str, current_prediction: float
    ) -> str:
        """Determine grade trend from recent snapshots."""
        result = (
            self.db.table("grade_snapshots")
            .select("predicted_grade")
            .eq("user_id", user_id)
            .eq("course_id", course_id)
            .neq("snapshot_type", "calibration")
            .order("created_at", desc=True)
            .limit(3)
            .execute()
        )

        if not result.data or len(result.data) < 2:
            return "new"

        prev_grades = [float(s["predicted_grade"]) for s in result.data]
        prev_avg = sum(prev_grades) / len(prev_grades)

        if current_prediction > prev_avg + 1:
            return "improving"
        elif current_prediction < prev_avg - 1:
            return "declining"
        return "stable"
