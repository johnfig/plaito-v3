"""Course listing and management endpoints."""

from fastapi import APIRouter, Depends

from app.dependencies import get_current_user, get_db

router = APIRouter(prefix="/api/v1", tags=["courses"])


@router.get("/courses")
def list_courses(
    user_id: str = Depends(get_current_user),
    db=Depends(get_db),
):
    """List all courses for the current user."""
    result = (
        db.table("courses")
        .select("*")
        .eq("user_id", user_id)
        .execute()
    )
    return {"courses": result.data or []}


@router.get("/user/profile")
def get_profile(
    user_id: str = Depends(get_current_user),
    db=Depends(get_db),
):
    """Get user profile."""
    result = (
        db.table("users")
        .select("*")
        .eq("id", user_id)
        .maybe_single()
        .execute()
    )
    return {"user": result.data}
