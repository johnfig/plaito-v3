"""Tests for the knowledge graph processor."""

from math import exp

from app.engines.knowledge_graph import (
    DECAY_LAMBDA,
    EMA_ALPHA,
    KnowledgeGraphProcessor,
)
from tests.conftest import (
    CONCEPT_IDS,
    COURSE_ID,
    USER_ID,
    make_concepts,
    make_mastery_scores,
)


class TestConfidence:
    def test_confidence_at_zero_attempts(self):
        assert KnowledgeGraphProcessor.calculate_confidence(0) == 0.0

    def test_confidence_at_one_attempt(self):
        expected = round(min(1.0, 1.0 - exp(-0.3 * 1)), 3)
        assert KnowledgeGraphProcessor.calculate_confidence(1) == expected

    def test_confidence_at_five_attempts(self):
        result = KnowledgeGraphProcessor.calculate_confidence(5)
        assert 0.7 < result < 0.85  # ~0.777

    def test_confidence_at_ten_attempts(self):
        result = KnowledgeGraphProcessor.calculate_confidence(10)
        assert result > 0.9  # ~0.950

    def test_confidence_caps_at_one(self):
        result = KnowledgeGraphProcessor.calculate_confidence(100)
        assert result == 1.0


class TestDecay:
    def test_no_decay_same_day(self):
        from datetime import datetime, timezone
        now = datetime.now(timezone.utc).isoformat()
        score, days = KnowledgeGraphProcessor.apply_decay(0.9, now)
        assert score == 0.9
        assert days == 0

    def test_decay_after_seven_days(self):
        from datetime import datetime, timedelta, timezone
        seven_days_ago = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()
        score, days = KnowledgeGraphProcessor.apply_decay(1.0, seven_days_ago)
        expected = round(exp(-DECAY_LAMBDA * 7), 3)
        assert score == expected
        assert days == 7

    def test_decay_after_fourteen_days(self):
        from datetime import datetime, timedelta, timezone
        fourteen_days_ago = (datetime.now(timezone.utc) - timedelta(days=14)).isoformat()
        score, days = KnowledgeGraphProcessor.apply_decay(1.0, fourteen_days_ago)
        assert 0.45 < score < 0.55  # ~0.497
        assert days == 14

    def test_no_decay_when_no_timestamp(self):
        score, days = KnowledgeGraphProcessor.apply_decay(0.8, None)
        assert score == 0.8
        assert days is None


class TestMasteryMap:
    def test_mastery_map_returns_all_concepts(self, mock_db, sample_concepts, sample_mastery):
        mock_db.set_table_data("concepts", sample_concepts)
        mock_db.set_table_data("mastery_scores", sample_mastery)

        kg = KnowledgeGraphProcessor(mock_db)
        result = kg.get_mastery_map(USER_ID, COURSE_ID)

        assert len(result) == 5

    def test_mastery_map_includes_unscored_concepts(self, mock_db, sample_concepts):
        mock_db.set_table_data("concepts", sample_concepts)
        mock_db.set_table_data("mastery_scores", [])

        kg = KnowledgeGraphProcessor(mock_db)
        result = kg.get_mastery_map(USER_ID, COURSE_ID)

        assert all(c["confidence"] == 0 for c in result)
        assert all(c["effective_score"] == 0.0 for c in result)


class TestGaps:
    def test_gaps_below_threshold(self, mock_db, sample_concepts, sample_mastery):
        mock_db.set_table_data("concepts", sample_concepts)
        mock_db.set_table_data("mastery_scores", sample_mastery)

        kg = KnowledgeGraphProcessor(mock_db)
        gaps = kg.get_concept_gaps(USER_ID, COURSE_ID, threshold=0.6)

        # Concepts with effective score < 0.6 after decay
        assert len(gaps) >= 2  # At least Series (0.3) and Limits (decayed)

    def test_gaps_sorted_by_weight(self, mock_db, sample_concepts, sample_mastery):
        mock_db.set_table_data("concepts", sample_concepts)
        mock_db.set_table_data("mastery_scores", sample_mastery)

        kg = KnowledgeGraphProcessor(mock_db)
        gaps = kg.get_concept_gaps(USER_ID, COURSE_ID, threshold=0.6)

        if len(gaps) > 1:
            for i in range(len(gaps) - 1):
                assert gaps[i]["weight"] >= gaps[i + 1]["weight"]


class TestStrengths:
    def test_strengths_above_threshold(self, mock_db, sample_concepts, sample_mastery):
        mock_db.set_table_data("concepts", sample_concepts)
        mock_db.set_table_data("mastery_scores", sample_mastery)

        kg = KnowledgeGraphProcessor(mock_db)
        strengths = kg.get_strengths(USER_ID, COURSE_ID, threshold=0.8)

        # Derivatives at 0.9 with 1 day decay should still be above 0.8
        assert len(strengths) >= 1
        assert all(s["effective_score"] >= 0.8 for s in strengths)


class TestEMA:
    def test_ema_calculation(self):
        old_score = 0.5
        signal = 1.0
        expected = EMA_ALPHA * signal + (1 - EMA_ALPHA) * old_score
        assert round(expected, 2) == 0.65
