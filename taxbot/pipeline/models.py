"""Data models for the pipeline."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class Concept:
    """Represents a DIAN concept."""

    title: str
    date: datetime
    theme: str
    descriptor: str
    link: str
    full_text: str
    summary: Optional[str] = None
    analysis: Optional[str] = None

    def to_record(self) -> dict[str, str]:
        """Convert concept to dictionary record."""
        return {
            "title": self.title,
            "date": self.date.strftime("%Y-%m-%d"),
            "theme": self.theme,
            "descriptor": self.descriptor,
            "link": self.link,
            "summary": self.summary or "",
            "analysis": self.analysis or "",
        }
