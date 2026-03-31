"""Knowledge graph processor — manages concept mastery scores."""

from __future__ import annotations

from datetime import datetime, timezone
from math import exp
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from supabase import Client


# Exponential moving average learning rate.
# Recent signals weigh 30% vs 70% history.
EMA_ALPHA = 0.3

# Spaced-repetition decay constant.
# After 14 days ≈ 50% retention, 7 days ≈ 70%, 1 day ≈ 95%.
DECAY_LAMBDA = 0.05


class KnowledgeGraphProcessor:
    def __init__(self, db: Any):
        self.db = db

    # ------------------------------------------------------------------
    # Mastery updates
    # ------------------------------------------------------------------

    def update_mastery_from_signal(
        self,
        user_id: str,
        concept_id: str,
        signal_type: str,
        signal_value: float,
        session_id: str | None = None,
    ) -> dict:
        """Update mastery score for a concept using exponential moving average.

        signal_type: correct_answer | incorrect_answer | needed_hint | confusion_detected
        signal_value: 0.0-1.0 (1.0 = perfect demonstration)
        """
        # Fetch existing mastery or create new
        existing = (
            self.db.table("mastery_scores")
            .select("*")
            .eq("user_id", user_id)
            .eq("concept_id", concept_id)
            .maybe_single()
            .execute()
        )

        now = datetime.now(timezone.utc).isoformat()

        if existing.data:
            old_score = float(existing.data["score"])
            old_confidence = float(existing.data["confidence"])
            attempt_count = existing.data["attempt_count"] + 1

            # EMA update
            new_score = EMA_ALPHA * signal_value + (1 - EMA_ALPHA) * old_score
            new_confidence = self.calculate_confidence(attempt_count)

            self.db.table("mastery_scores").update({
                "score": round(new_score, 3),
                "confidence": round(new_confidence, 3),
                "attempt_count": attempt_count,
                "last_practiced_at": now,
                "updated_at": now,
            }).eq("id", existing.data["id"]).execute()

            # Append to history
            self.db.table("mastery_history").insert({
                "mastery_score_id": existing.data["id"],
                "score": round(new_score, 3),
                "confidence": round(new_confidence, 3),
                "source": "session",
                "session_id": session_id,
            }).execute()

            return {
                "concept_id": concept_id,
                "old_score": old_score,
                "new_score": round(new_score, 3),
                "new_confidence": round(new_confidence, 3),
                "attempt_count": attempt_count,
            }
        else:
            # First interaction with this concept
            new_score = signal_value
            new_confidence = self.calculate_confidence(1)

            result = self.db.table("mastery_scores").insert({
                "user_id": user_id,
                "concept_id": concept_id,
                "score": round(new_score, 3),
                "confidence": round(new_confidence, 3),
                "attempt_count": 1,
                "last_practiced_at": now,
            }).execute()

            # Append to history
            if result.data:
                self.db.table("mastery_history").insert({
                    "mastery_score_id": result.data[0]["id"],
                    "score": round(new_score, 3),
                    "confidence": round(new_confidence, 3),
                    "source": "session",
                    "session_id": session_id,
                }).execute()

            return {
                "concept_id": concept_id,
                "old_score": 0.0,
                "new_score": round(new_score, 3),
                "new_confidence": round(new_confidence, 3),
                "attempt_count": 1,
            }

    # ------------------------------------------------------------------
    # Confidence calculation
    # ------------------------------------------------------------------

    @staticmethod
    def calculate_confidence(attempt_count: int) -> float:
        """Confidence ramps up with attempts: min(1.0, 1 - e^(-0.3 * n))."""
        return round(min(1.0, 1.0 - exp(-0.3 * attempt_count)), 3)

    # ------------------------------------------------------------------
    # Decay
    # ------------------------------------------------------------------

    @staticmethod
    def apply_decay(score: float, last_practiced_at: str | None) -> tuple[float, int | None]:
        """Apply spaced-repetition decay. Returns (decayed_score, days_since)."""
        if not last_practiced_at:
            return score, None

        last_dt = datetime.fromisoformat(last_practiced_at.replace("Z", "+00:00"))
        now = datetime.now(timezone.utc)
        days_since = max(0, (now - last_dt).days)

        decay_factor = exp(-DECAY_LAMBDA * days_since)
        return round(score * decay_factor, 3), days_since

    # ------------------------------------------------------------------
    # Mastery map
    # ------------------------------------------------------------------

    def get_mastery_map(self, user_id: str, course_id: str) -> list[dict]:
        """Return all concepts for a course with decay-adjusted mastery."""
        concepts = (
            self.db.table("concepts")
            .select("*")
            .eq("course_id", course_id)
            .execute()
        )

        mastery_rows = (
            self.db.table("mastery_scores")
            .select("*")
            .eq("user_id", user_id)
            .execute()
        )
        mastery_by_concept = {
            row["concept_id"]: row for row in (mastery_rows.data or [])
        }

        results = []
        for concept in (concepts.data or []):
            mastery = mastery_by_concept.get(concept["id"])
            if mastery:
                effective_score, days_since = self.apply_decay(
                    float(mastery["score"]),
                    mastery.get("last_practiced_at"),
                )
                results.append({
                    "concept_id": concept["id"],
                    "concept_name": concept["name"],
                    "weight": float(concept["weight"]),
                    "raw_score": float(mastery["score"]),
                    "effective_score": effective_score,
                    "confidence": float(mastery["confidence"]),
                    "attempt_count": mastery["attempt_count"],
                    "days_since_practice": days_since,
                })
            else:
                results.append({
                    "concept_id": concept["id"],
                    "concept_name": concept["name"],
                    "weight": float(concept["weight"]),
                    "raw_score": 0.0,
                    "effective_score": 0.0,
                    "confidence": 0.0,
                    "attempt_count": 0,
                    "days_since_practice": None,
                })

        return results

    # ------------------------------------------------------------------
    # Gaps and strengths
    # ------------------------------------------------------------------

    def get_concept_gaps(
        self, user_id: str, course_id: str, threshold: float = 0.6
    ) -> list[dict]:
        """Concepts below threshold mastery, sorted by weight descending."""
        mastery_map = self.get_mastery_map(user_id, course_id)
        gaps = [c for c in mastery_map if c["effective_score"] < threshold]
        gaps.sort(key=lambda c: c["weight"], reverse=True)
        return gaps

    def get_strengths(
        self, user_id: str, course_id: str, threshold: float = 0.8
    ) -> list[dict]:
        """Concepts above threshold mastery, sorted by effective score descending."""
        mastery_map = self.get_mastery_map(user_id, course_id)
        strengths = [
            c for c in mastery_map
            if c["effective_score"] >= threshold and c["confidence"] > 0
        ]
        strengths.sort(key=lambda c: c["effective_score"], reverse=True)
        return strengths
