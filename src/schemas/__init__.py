"""Pydantic schemas for data contracts between agents."""

from .faculty import FacultyProfile
from .research import EnrichedProfile, Publication
from .cv import (
    StudentCV, Education, Project, ResearchExperience,
    Internship, Competition, Skills, Coursework, Extracurriculars
)
from .output import EmailOutput, MatchReason

__all__ = [
    "FacultyProfile",
    "EnrichedProfile",
    "Publication",
    "StudentCV",
    "Education",
    "Project",
    "ResearchExperience",
    "Internship",
    "Competition",
    "Skills",
    "Coursework",
    "Extracurriculars",
    "EmailOutput",
    "MatchReason",
]

