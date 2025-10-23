"""Domain models for DIAN concepts."""

from __future__ import annotations

import re
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, validator


class Concept(BaseModel):
    """DIAN concept domain model."""

    title: str = Field(..., description="Concept title")
    date: datetime = Field(..., description="Publication date")
    theme: str = Field(..., description="Concept theme/category")
    descriptor: str = Field(..., description="Concept descriptor")
    link: str = Field(..., description="URL to the concept")
    full_text: str = Field(default="", description="Full text content")
    summary: Optional[str] = Field(default=None, description="AI-generated summary")
    analysis: Optional[str] = Field(default=None, description="AI-generated analysis")

    @validator("title")
    def validate_title(cls, v: str) -> str:
        """Validate and clean title."""
        if not v or not v.strip():
            raise ValueError("Title cannot be empty")
        return v.strip()

    @validator("theme")
    def validate_theme(cls, v: str) -> str:
        """Validate and clean theme."""
        if not v or not v.strip():
            return "Sin tema"
        return v.strip()

    @validator("descriptor")
    def validate_descriptor(cls, v: str) -> str:
        """Validate and clean descriptor."""
        return v.strip() if v else ""

    @validator("link")
    def validate_link(cls, v: str) -> str:
        """Validate URL format."""
        if not v or not v.strip():
            raise ValueError("Link cannot be empty")
        
        # Basic URL validation
        url_pattern = re.compile(
            r"^https?://"  # http:// or https://
            r"(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|"  # domain...
            r"localhost|"  # localhost...
            r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})"  # ...or ip
            r"(?::\d+)?"  # optional port
            r"(?:/?|[/?]\S+)$",
            re.IGNORECASE,
        )
        
        if not url_pattern.match(v):
            raise ValueError("Invalid URL format")
        
        return v.strip()

    @validator("full_text")
    def validate_full_text(cls, v: str) -> str:
        """Validate and clean full text."""
        return v.strip() if v else ""

    @validator("summary")
    def validate_summary(cls, v: Optional[str]) -> Optional[str]:
        """Validate and clean summary."""
        return v.strip() if v else None

    @validator("analysis")
    def validate_analysis(cls, v: Optional[str]) -> Optional[str]:
        """Validate and clean analysis."""
        return v.strip() if v else None

    def to_record(self) -> dict[str, str]:
        """Convert to dictionary for CSV storage."""
        return {
            "title": self.title,
            "date": self.date.strftime("%Y-%m-%d"),
            "theme": self.theme,
            "descriptor": self.descriptor,
            "link": self.link,
            "summary": self.summary or "",
            "analysis": self.analysis or "",
        }

    @classmethod
    def from_record(cls, record: dict[str, str]) -> Concept:
        """Create from dictionary record."""
        return cls(
            title=record.get("title", ""),
            date=datetime.strptime(record.get("date", "1900-01-01"), "%Y-%m-%d"),
            theme=record.get("theme", "Sin tema"),
            descriptor=record.get("descriptor", ""),
            link=record.get("link", ""),
            summary=record.get("summary") or None,
            analysis=record.get("analysis") or None,
        )

    def has_ai_content(self) -> bool:
        """Check if concept has AI-generated content."""
        return bool(self.summary and self.analysis)

    def is_processed(self) -> bool:
        """Check if concept has been fully processed."""
        return bool(self.full_text and self.summary and self.analysis)

    def get_content_preview(self, max_length: int = 200) -> str:
        """Get a preview of the content."""
        content = self.full_text or self.descriptor or self.title
        if len(content) <= max_length:
            return content
        return content[:max_length] + "..."

    class Config:
        """Pydantic configuration."""

        json_encoders = {
            datetime: lambda v: v.strftime("%Y-%m-%d %H:%M:%S"),
        }


class ConceptSearchRequest(BaseModel):
    """Request model for concept search."""

    query: str = Field(..., min_length=1, max_length=500, description="Search query")
    limit: int = Field(default=10, ge=1, le=100, description="Maximum results")
    offset: int = Field(default=0, ge=0, description="Results offset")
    theme: Optional[str] = Field(default=None, description="Filter by theme")
    date_from: Optional[datetime] = Field(default=None, description="Filter from date")
    date_to: Optional[datetime] = Field(default=None, description="Filter to date")

    @validator("query")
    def validate_query(cls, v: str) -> str:
        """Validate search query."""
        if not v or not v.strip():
            raise ValueError("Query cannot be empty")
        return v.strip()


class ConceptSearchResponse(BaseModel):
    """Response model for concept search."""

    concepts: list[Concept] = Field(..., description="Found concepts")
    total: int = Field(..., description="Total number of results")
    limit: int = Field(..., description="Results limit")
    offset: int = Field(..., description="Results offset")
    has_more: bool = Field(..., description="Whether there are more results")


class ConceptListResponse(BaseModel):
    """Response model for concept listing."""

    concepts: list[Concept] = Field(..., description="List of concepts")
    total: int = Field(..., description="Total number of concepts")
    limit: int = Field(..., description="Results limit")
    offset: int = Field(..., description="Results offset")
    has_more: bool = Field(..., description="Whether there are more results")


class ScrapingStatus(BaseModel):
    """Status of scraping operation."""

    is_running: bool = Field(..., description="Whether scraping is currently running")
    last_run: Optional[datetime] = Field(default=None, description="Last scraping run")
    total_concepts: int = Field(default=0, description="Total concepts in database")
    new_concepts: int = Field(default=0, description="New concepts in last run")
    errors: list[str] = Field(default_factory=list, description="Any errors encountered")

    class Config:
        """Pydantic configuration."""

        json_encoders = {
            datetime: lambda v: v.strftime("%Y-%m-%d %H:%M:%S"),
        }
