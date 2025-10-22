"""Admin API routes."""

from __future__ import annotations

import asyncio
from datetime import datetime
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import JSONResponse

from ...core.logging import get_api_logger
from ...models.concept import ScrapingStatus
from ...scrapers.dian_scraper import DianScraper
from ...storage.repository import Repository

router = APIRouter()
logger = get_api_logger()

# Global scraping status
_scraping_status = ScrapingStatus(
    is_running=False,
    last_run=None,
    total_concepts=0,
    new_concepts=0,
    errors=[]
)


def get_repository(request: Request) -> Repository:
    """Get repository from request state."""
    return request.app.state.repository


def verify_api_key(request: Request) -> bool:
    """Verify API key for admin endpoints."""
    api_key = request.headers.get("X-API-Key")
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key required"
        )
    
    # In production, use proper JWT validation
    from ...core.config import get_settings
    settings = get_settings()
    
    if api_key != settings.api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key"
        )
    
    return True


@router.post("/scrape", response_model=ScrapingStatus)
async def trigger_scraping(
    request: Request,
    repo: Repository = Depends(get_repository),
    _: bool = Depends(verify_api_key),
):
    """Trigger manual scraping."""
    global _scraping_status
    
    if _scraping_status.is_running:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Scraping is already running"
        )
    
    # Start scraping in background
    asyncio.create_task(_run_scraping(repo))
    
    _scraping_status.is_running = True
    _scraping_status.errors = []
    
    logger.info("Manual scraping triggered")
    return _scraping_status


@router.get("/status", response_model=ScrapingStatus)
async def get_scraping_status(
    request: Request = None,
    repo: Repository = Depends(get_repository),
):
    """Get current scraping status."""
    try:
        # Update status with current data
        _scraping_status.total_concepts = repo.get_concept_count()
        
        return _scraping_status
        
    except Exception as e:
        logger.error(f"Error getting scraping status: {e}")
        raise HTTPException(status_code=500, detail="Failed to get status")


@router.post("/reprocess")
async def reprocess_concepts(
    request: Request,
    repo: Repository = Depends(get_repository),
    _: bool = Depends(verify_api_key),
):
    """Reprocess concepts with AI analysis."""
    try:
        # Get all concepts without AI content
        concepts = repo.get_concepts(limit=1000)  # Adjust limit as needed
        concepts_to_process = [c for c in concepts if not c.has_ai_content()]
        
        if not concepts_to_process:
            return JSONResponse(
                content={"message": "No concepts need reprocessing"}
            )
        
        # Process with AI (this would need to be implemented)
        # For now, just return a message
        return JSONResponse(
            content={
                "message": f"Reprocessing {len(concepts_to_process)} concepts",
                "concepts_to_process": len(concepts_to_process)
            }
        )
        
    except Exception as e:
        logger.error(f"Error reprocessing concepts: {e}")
        raise HTTPException(status_code=500, detail="Failed to reprocess concepts")


@router.delete("/concepts/{concept_id}")
async def delete_concept(
    concept_id: str,
    request: Request = None,
    repo: Repository = Depends(get_repository),
    _: bool = Depends(verify_api_key),
):
    """Delete a concept."""
    try:
        success = repo.delete_concept(concept_id)
        if not success:
            raise HTTPException(status_code=404, detail="Concept not found")
        
        logger.info(f"Deleted concept: {concept_id}")
        return JSONResponse(content={"message": "Concept deleted successfully"})
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting concept {concept_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete concept")


@router.post("/backup")
async def create_backup(
    request: Request = None,
    repo: Repository = Depends(get_repository),
    _: bool = Depends(verify_api_key),
):
    """Create a backup of the database."""
    try:
        backup_path = repo.backup()
        
        logger.info(f"Created backup: {backup_path}")
        return JSONResponse(
            content={
                "message": "Backup created successfully",
                "backup_path": backup_path
            }
        )
        
    except Exception as e:
        logger.error(f"Error creating backup: {e}")
        raise HTTPException(status_code=500, detail="Failed to create backup")


async def _run_scraping(repo: Repository):
    """Run scraping process in background."""
    global _scraping_status
    
    try:
        logger.info("Starting scraping process")
        
        # Initialize scraper
        scraper = DianScraper()
        
        # Scrape concepts
        concepts = scraper.scrape_concepts()
        
        if not concepts:
            logger.warning("No concepts found during scraping")
            _scraping_status.errors.append("No concepts found")
            return
        
        # Filter new concepts
        existing_links = set()
        try:
            existing_concepts = repo.get_concepts(limit=10000)  # Get all for comparison
            existing_links = {c.link for c in existing_concepts}
        except Exception as e:
            logger.warning(f"Error getting existing concepts: {e}")
        
        new_concepts = [c for c in concepts if c.link not in existing_links]
        
        # Save new concepts
        if new_concepts:
            repo.save_concepts(new_concepts)
            _scraping_status.new_concepts = len(new_concepts)
            logger.info(f"Saved {len(new_concepts)} new concepts")
        else:
            logger.info("No new concepts to save")
        
        # Update status
        _scraping_status.last_run = datetime.utcnow()
        _scraping_status.total_concepts = repo.get_concept_count()
        
        logger.info("Scraping process completed successfully")
        
    except Exception as e:
        logger.error(f"Scraping process failed: {e}")
        _scraping_status.errors.append(str(e))
        
    finally:
        _scraping_status.is_running = False
