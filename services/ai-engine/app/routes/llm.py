"""LLM completion endpoints — DeepSeek V3/R1 routing."""

from fastapi import APIRouter, Depends

from app.dependencies import get_llm
from app.engines.llm_router import LLMRouter
from app.models.schemas import (
    AnalyzeRequest,
    AnalyzeResponse,
    ExtractConceptsRequest,
    ExtractConceptsResponse,
    LLMCompleteRequest,
    LLMCompleteResponse,
)

router = APIRouter(prefix="/api/v1/llm", tags=["llm"])


@router.post("/complete", response_model=LLMCompleteResponse)
async def llm_complete(
    request: LLMCompleteRequest,
    llm: LLMRouter = Depends(get_llm),
):
    """General LLM completion. task_type='standard' (V3) or 'reasoning' (R1)."""
    result = await llm.complete(
        prompt=request.prompt,
        task_type=request.task_type,
        system_prompt=request.system_prompt,
        max_tokens=request.max_tokens,
    )
    return LLMCompleteResponse(**result)


@router.post("/extract-concepts", response_model=ExtractConceptsResponse)
async def extract_concepts(
    request: ExtractConceptsRequest,
    llm: LLMRouter = Depends(get_llm),
):
    """Extract educational concepts from text using DeepSeek V3."""
    concepts = await llm.extract_concepts(
        text=request.text,
        course_name=request.course_name,
    )
    return ExtractConceptsResponse(
        concepts=concepts,
        course_name=request.course_name,
    )


@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze(
    request: AnalyzeRequest,
    llm: LLMRouter = Depends(get_llm),
):
    """Deep analysis using DeepSeek R1 (reasoning model)."""
    result = await llm.analyze(
        prompt=request.prompt,
        context=request.context,
        max_tokens=request.max_tokens,
    )
    return AnalyzeResponse(
        analysis=result["content"],
        model=result["model"],
    )
