"""Research enrichment schema for Agent 2 (Research Enrichment)."""

from pydantic import BaseModel, Field
from typing import List, Optional


class Publication(BaseModel):
    """Represents a single academic publication."""
    
    title: str = Field(..., description="Publication title")
    authors: List[str] = Field(default_factory=list, description="List of authors")
    venue: Optional[str] = Field(None, description="Journal or conference name")
    year: Optional[int] = Field(None, description="Publication year")
    url: Optional[str] = Field(None, description="Link to publication")


class EnrichedProfile(BaseModel):
    """
    Enriched faculty profile with additional research data.
    
    This extends the base FacultyProfile with research-specific information
    gathered from web searches and Google Scholar.
    """
    
    # Base faculty data (copied from FacultyProfile)
    name: str = Field(..., description="Full name of the faculty member")
    designation: str = Field(..., description="Academic designation")
    department: str = Field(..., description="Department name")
    email: Optional[str] = Field(None, description="Email address")
    phone: Optional[str] = Field(None, description="Phone number")
    profile_url: str = Field(..., description="URL to faculty profile page")
    bio: Optional[str] = Field(None, description="Bio sketch")
    education: Optional[str] = Field(None, description="Educational qualifications")
    personal_webpage: Optional[str] = Field(None, description="Personal webpage URL")
    
    # Enriched research data
    research_areas: List[str] = Field(
        default_factory=list, 
        description="Research areas/interests (enriched)"
    )
    recent_publications: List[Publication] = Field(
        default_factory=list, 
        description="Recent publications from profile/Scholar"
    )
    current_projects: List[str] = Field(
        default_factory=list, 
        description="Current research projects"
    )
    scholar_links: List[str] = Field(
        default_factory=list, 
        description="Google Scholar, DBLP, ResearchGate links"
    )
    expertise_keywords: List[str] = Field(
        default_factory=list, 
        description="Extracted expertise keywords for matching"
    )
    enrichment_confidence: float = Field(
        default=0.0, 
        ge=0.0, 
        le=1.0,
        description="Confidence score for enriched data (0-1)"
    )
    
    @classmethod
    def from_faculty_profile(cls, profile: "FacultyProfile") -> "EnrichedProfile":
        """Create an EnrichedProfile from a base FacultyProfile."""
        return cls(
            name=profile.name,
            designation=profile.designation,
            department=profile.department,
            email=profile.email,
            phone=profile.phone,
            profile_url=profile.profile_url,
            bio=profile.bio,
            education=profile.education,
            personal_webpage=profile.personal_webpage,
            research_areas=profile.research_areas.copy() if profile.research_areas else [],
        )


# Import here to avoid circular imports
from .faculty import FacultyProfile
