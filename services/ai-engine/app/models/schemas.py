from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Domain models
# ---------------------------------------------------------------------------

class Concept(BaseModel):
    id: UUID
    course_id: UUID
    name: str
    description: str | None = None
    weight: float = 1.0
    parent_concept_id: UUID | None = None


class MasteryScore(BaseModel):
    id: UUID
    user_id: UUID
    concept_id: UUID
    score: float = 0.0          # 0-1 internal scale
    confidence: float = 0.0     # 0-1
    attempt_count: int = 0
    last_practiced_at: datetime | None = None


class GradeFactor(BaseModel):
    concept_name: str
    concept_id: UUID
    weight: float
    effective_mastery: float    # after decay
    impact: float               # how much this drags/boosts the grade
    days_since_practice: int | None = None


class GradePrediction(BaseModel):
    predicted_grade: float              # 0-100
    predicted_letter: str               # A, B+, etc.
    confidence: float                   # 0-1
    factors: list[GradeFactor]
    recommended_actions: list[str]
    sessions_to_target: int | None = None
    trend: str = "new"                  # improving, stable, declining, new


# ---------------------------------------------------------------------------
# Request models
# ---------------------------------------------------------------------------

class ReportActualGradeRequest(BaseModel):
    actual_grade: float = Field(ge=0, le=100)
    assessment_type: str = "general"    # test, quiz, midterm, final, general


class UpdateMasteryRequest(BaseModel):
    user_id: UUID
    concept_id: UUID
    signal_type: str            # correct_answer, incorrect_answer, needed_hint, confusion_detected
    signal_value: float = Field(ge=0.0, le=1.0)
    session_id: UUID | None = None


class LLMCompleteRequest(BaseModel):
    prompt: str
    system_prompt: str | None = None
    task_type: str = "standard"         # standard (V3) or reasoning (R1)
    max_tokens: int = 2048


class ExtractConceptsRequest(BaseModel):
    text: str
    course_name: str | None = None


class AnalyzeRequest(BaseModel):
    prompt: str
    context: dict | None = None
    max_tokens: int = 4096


# ---------------------------------------------------------------------------
# Response models
# ---------------------------------------------------------------------------

class GradePredictionResponse(BaseModel):
    prediction: GradePrediction
    course_id: UUID
    snapshot_id: UUID | None = None


class MasteryMapResponse(BaseModel):
    course_id: UUID
    concepts: list[dict]        # [{concept, mastery, confidence, days_since, ...}]
    gaps: list[dict]            # concepts below threshold
    strengths: list[dict]       # concepts above threshold
    overall_mastery: float      # 0-100


class GradeHistoryResponse(BaseModel):
    course_id: UUID
    snapshots: list[dict]       # [{date, predicted_grade, predicted_letter, confidence}]


class MasteryUpdateResponse(BaseModel):
    concept_id: UUID
    old_score: float
    new_score: float
    new_confidence: float
    attempt_count: int


class LLMCompleteResponse(BaseModel):
    content: str
    model: str
    usage: dict | None = None


class ExtractConceptsResponse(BaseModel):
    concepts: list[dict]        # [{name, description, estimated_weight}]
    course_name: str | None = None


class AnalyzeResponse(BaseModel):
    analysis: str
    model: str
