"""Concepts API routes."""

from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import JSONResponse

from ...core.logging import get_api_logger
from ...models.concept import Concept, ConceptSearchRequest, ConceptSearchResponse
from ...storage.repository import Repository

router = APIRouter()
logger = get_api_logger()


def get_repository(request) -> Repository:
    """Get repository from request state."""
    return request.app.state.repository


@router.get("/concepts", response_model=List[Concept])
async def list_concepts(
    limit: int = Query(default=10, ge=1, le=100, description="Maximum results"),
    offset: int = Query(default=0, ge=0, description="Results offset"),
    theme: Optional[str] = Query(default=None, description="Filter by theme"),
    request: Request = None,
    repo: Repository = Depends(get_repository),
):
    """List concepts with pagination and filtering."""
    try:
        concepts = repo.get_concepts(
            limit=limit,
            offset=offset,
            theme=theme,
        )
        
        logger.info(f"Retrieved {len(concepts)} concepts")
        return concepts
        
    except Exception as e:
        logger.error(f"Error listing concepts: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve concepts")


@router.get("/concepts/{concept_id}", response_model=Concept)
async def get_concept(
    concept_id: str,
    request: Request = None,
    repo: Repository = Depends(get_repository),
):
    """Get a specific concept by ID."""
    try:
        concept = repo.get_concept_by_id(concept_id)
        if not concept:
            raise HTTPException(status_code=404, detail="Concept not found")
        
        logger.info(f"Retrieved concept: {concept_id}")
        return concept
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting concept {concept_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve concept")


@router.post("/concepts/search", response_model=ConceptSearchResponse)
async def search_concepts(
    request: ConceptSearchRequest,
    repo: Repository = Depends(get_repository),
):
    """Search concepts with full-text search."""
    try:
        response = repo.search_concepts(request)
        
        logger.info(f"Search for '{request.query}' returned {len(response.concepts)} results")
        return response
        
    except Exception as e:
        logger.error(f"Error searching concepts: {e}")
        raise HTTPException(status_code=500, detail="Search failed")


@router.get("/concepts/themes", response_model=List[str])
async def get_themes(
    request: Request = None,
    repo: Repository = Depends(get_repository),
):
    """Get list of unique themes."""
    try:
        themes = repo.get_themes()
        
        logger.info(f"Retrieved {len(themes)} themes")
        return themes
        
    except Exception as e:
        logger.error(f"Error getting themes: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve themes")


@router.get("/concepts/latest", response_model=List[Concept])
async def get_latest_concepts(
    limit: int = Query(default=10, ge=1, le=100, description="Maximum results"),
    request: Request = None,
    repo: Repository = Depends(get_repository),
):
    """Get latest concepts by date."""
    try:
        concepts = repo.get_latest_concepts(limit=limit)
        
        logger.info(f"Retrieved {len(concepts)} latest concepts")
        return concepts
        
    except Exception as e:
        logger.error(f"Error getting latest concepts: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve latest concepts")
