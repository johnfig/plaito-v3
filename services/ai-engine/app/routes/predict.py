"""Grade prediction endpoints."""

from fastapi import APIRouter, Depends, Query

from app.dependencies import get_current_user, get_db
from app.engines.grade_predictor import GradePredictor
from app.models.schemas import (
    GradeHistoryResponse,
    GradePredictionResponse,
    ReportActualGradeRequest,
)

router = APIRouter(prefix="/api/v1/grades", tags=["grades"])


@router.get("/{course_id}/predict", response_model=GradePredictionResponse)
def predict_grade(
    course_id: str,
    save: bool = Query(default=True),
    user_id: str = Depends(get_current_user),
    db=Depends(get_db),
):
    predictor = GradePredictor(db)
    prediction = predictor.predict(user_id, course_id)

    snapshot_id = None
    if save:
        snapshot_id = predictor.save_snapshot(user_id, course_id, prediction)

    return GradePredictionResponse(
        prediction=prediction,
        course_id=course_id,
        snapshot_id=snapshot_id,
    )


@router.get("/{course_id}/history", response_model=GradeHistoryResponse)
def grade_history(
    course_id: str,
    limit: int = Query(default=30, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    user_id: str = Depends(get_current_user),
    db=Depends(get_db),
):
    predictor = GradePredictor(db)
    snapshots = predictor.get_history(user_id, course_id, limit=limit, offset=offset)

    return GradeHistoryResponse(
        course_id=course_id,
        snapshots=snapshots,
    )


@router.post("/{course_id}/report-actual")
def report_actual_grade(
    course_id: str,
    request: ReportActualGradeRequest,
    user_id: str = Depends(get_current_user),
    db=Depends(get_db),
):
    predictor = GradePredictor(db)
    result = predictor.report_actual_grade(user_id, course_id, request.actual_grade)
    return result
