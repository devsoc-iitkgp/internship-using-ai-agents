"""LangGraph state definition for the agent pipeline."""

from typing import TypedDict, List, Optional, Annotated
from operator import add

from ..schemas.faculty import FacultyProfile
from ..schemas.research import EnrichedProfile
from ..schemas.cv import StudentCV
from ..schemas.output import EmailOutput


class AgentState(TypedDict):
    """
    State object passed between agents in the LangGraph workflow.
    
    This TypedDict defines the complete state schema for the pipeline.
    Each agent reads from and writes to specific fields.
    """
    
    # === Input Configuration ===
    faculty_url: str  # URL to faculty directory
    cv_path: Optional[str]  # Path to student CV file
    target_departments: Optional[List[str]]  # Filter by departments
    faculty_limit: Optional[int]  # Limit number of faculty to process
    min_match_score: float  # Minimum match score for email generation
    
    # === Agent 1 Output: Faculty Scraper ===
    faculty_profiles: List[FacultyProfile]  # Scraped faculty profiles
    
    # === Agent 2 Output: Research Enrichment ===
    enriched_profiles: List[EnrichedProfile]  # Enriched profiles with research data
    
    # === Agent 3 Output: CV Parser ===
    student_cv: Optional[StudentCV]  # Parsed student CV
    
    # === Agent 4 Output: Personalization ===
    email_outputs: List[EmailOutput]  # Generated emails and cover letters
    
    # === Execution Metadata ===
    errors: Annotated[List[str], add]  # Errors accumulated during execution
    logs: Annotated[List[str], add]  # Log messages from agents
    current_step: str  # Current execution step
    completed_steps: List[str]  # List of completed steps
    
    
def create_initial_state(
    cv_path: Optional[str] = None,
    target_departments: Optional[List[str]] = None,
    faculty_limit: Optional[int] = None,
    min_match_score: float = 0.3
) -> AgentState:
    """
    Create initial state for pipeline execution.
    
    Args:
        cv_path: Optional path to student CV file
        target_departments: Optional list of departments to filter
        faculty_limit: Optional limit on faculty to scrape
        min_match_score: Minimum match score for generating emails
        
    Returns:
        Initialized AgentState
    """
    from ..utils.config import settings
    
    return AgentState(
        faculty_url=settings.faculty_list_url,
        cv_path=cv_path,
        target_departments=target_departments,
        faculty_limit=faculty_limit,
        min_match_score=min_match_score,
        faculty_profiles=[],
        enriched_profiles=[],
        student_cv=None,
        email_outputs=[],
        errors=[],
        logs=[],
        current_step="initialized",
        completed_steps=[]
    )
