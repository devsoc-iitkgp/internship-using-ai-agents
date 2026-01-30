"""Faculty profile schema for Agent 1 (Faculty Scraper)."""

from pydantic import BaseModel, EmailStr, HttpUrl, Field
from typing import Optional, List


class FacultyProfile(BaseModel):
    """
    Represents a faculty member's profile scraped from IIT KGP website.
    
    This is the output schema for Agent 1 (Faculty Scraper).
    """
    
    name: str = Field(..., description="Full name of the faculty member")
    designation: str = Field(..., description="Academic designation (Professor, Associate Professor, etc.)")
    department: str = Field(..., description="Department name")
    email: Optional[str] = Field(None, description="Email address")
    phone: Optional[str] = Field(None, description="Phone number")
    profile_url: str = Field(..., description="URL to faculty profile page")
    bio: Optional[str] = Field(None, description="Bio sketch or about section")
    education: Optional[str] = Field(None, description="Educational qualifications")
    research_areas: List[str] = Field(default_factory=list, description="List of research areas/interests")
    personal_webpage: Optional[str] = Field(None, description="Personal or lab webpage URL")
    
    class Config:
        json_schema_extra = {
            "example": {
                "name": "Debdeep Mukhopadhyay",
                "designation": "Professor",
                "department": "Computer Science and Engineering",
                "email": "debdeep@cse.iitkgp.ac.in",
                "phone": "+91-3222-282350",
                "profile_url": "https://www.iitkgp.ac.in/department/CS/faculty/cs-debdeep",
                "bio": "Research interests in hardware security, cryptography...",
                "education": "Ph.D., IISc Bangalore",
                "research_areas": ["Hardware Security", "Cryptography", "VLSI Design"],
                "personal_webpage": "https://cse.iitkgp.ac.in/~debdeep/"
            }
        }
