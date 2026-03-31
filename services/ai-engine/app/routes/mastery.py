"""Mastery map and update endpoints."""

from fastapi import APIRouter, Depends

from app.dependencies import get_current_user, get_db
from app.engines.knowledge_graph import KnowledgeGraphProcessor
from app.models.schemas import (
    MasteryMapResponse,
    MasteryUpdateResponse,
    UpdateMasteryRequest,
)

router = APIRouter(prefix="/api/v1", tags=["mastery"])


@router.get("/courses/{course_id}/mastery", response_model=MasteryMapResponse)
def get_mastery_map(
    course_id: str,
    user_id: str = Depends(get_current_user),
    db=Depends(get_db),
):
    kg = KnowledgeGraphProcessor(db)
    mastery_map = kg.get_mastery_map(user_id, course_id)
    gaps = kg.get_concept_gaps(user_id, course_id)
    strengths = kg.get_strengths(user_id, course_id)

    total_score = sum(c["effective_score"] for c in mastery_map)
    overall = (total_score / len(mastery_map) * 100) if mastery_map else 0.0

    return MasteryMapResponse(
        course_id=course_id,
        concepts=mastery_map,
        gaps=gaps,
        strengths=strengths,
        overall_mastery=round(overall, 1),
    )


@router.post("/mastery/update", response_model=MasteryUpdateResponse)
def update_mastery(
    request: UpdateMasteryRequest,
    db=Depends(get_db),
):
    kg = KnowledgeGraphProcessor(db)
    result = kg.update_mastery_from_signal(
        user_id=str(request.user_id),
        concept_id=str(request.concept_id),
        signal_type=request.signal_type,
        signal_value=request.signal_value,
        session_id=str(request.session_id) if request.session_id else None,
    )

    return MasteryUpdateResponse(
        concept_id=request.concept_id,
        old_score=result["old_score"],
        new_score=result["new_score"],
        new_confidence=result["new_confidence"],
        attempt_count=result["attempt_count"],
    )
