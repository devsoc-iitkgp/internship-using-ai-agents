"""Output schema for Agent 4 (Personalization & Writing)."""

from pydantic import BaseModel, Field
from typing import List, Optional


class MatchReason(BaseModel):
    """Represents a single match between student and professor profiles."""
    
    category: str = Field(
        ..., 
        description="Match category: 'skill', 'project', 'research_area', 'publication'"
    )
    student_item: str = Field(
        ..., 
        description="The student's skill/project/interest that matches"
    )
    professor_item: str = Field(
        ..., 
        description="The professor's research area/project that matches"
    )
    relevance_score: float = Field(
        ..., 
        ge=0.0, 
        le=1.0,
        description="Relevance score for this match (0-1)"
    )
    explanation: str = Field(
        default="", 
        description="Brief explanation of why this is a good match"
    )


class EmailOutput(BaseModel):
    """
    Final output for a professor-student pair.
    
    Contains the matching analysis and generated outreach content.
    """
    
    # Professor info
    professor_name: str = Field(..., description="Professor's full name")
    professor_email: Optional[str] = Field(None, description="Professor's email")
    department: str = Field(..., description="Professor's department")
    profile_url: str = Field(..., description="Professor's profile URL")
    
    # Matching analysis
    match_reasons: List[MatchReason] = Field(
        default_factory=list,
        description="List of reasons why this is a good match"
    )
    overall_match_score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Overall match score (0-1)"
    )
    
    # Generated content
    email_subject: str = Field(..., description="Email subject line")
    email_body: str = Field(..., description="Email body content")
    cover_letter: str = Field(..., description="Cover letter content (1 page max)")
    
    # Metadata
    generated_at: str = Field(default="", description="Timestamp of generation")
    model_used: str = Field(default="", description="LLM model used for generation")
    
    class Config:
        json_schema_extra = {
            "example": {
                "professor_name": "Debdeep Mukhopadhyay",
                "professor_email": "debdeep@cse.iitkgp.ac.in",
                "department": "Computer Science and Engineering",
                "profile_url": "https://www.iitkgp.ac.in/department/CS/faculty/cs-debdeep",
                "match_reasons": [
                    {
                        "category": "skill",
                        "student_item": "FPGA Development",
                        "professor_item": "Hardware Security",
                        "relevance_score": 0.85,
                        "explanation": "FPGA skills directly applicable to hardware security research"
                    }
                ],
                "overall_match_score": 0.82,
                "email_subject": "Research Internship Inquiry - Hardware Security",
                "email_body": "Dear Professor Mukhopadhyay...",
                "cover_letter": "..."
            }
        }
