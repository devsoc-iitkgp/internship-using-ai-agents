"""LangGraph workflow definition for agent orchestration."""

import asyncio
from typing import Optional, List, Dict, Any

from langgraph.graph import StateGraph, END

from .state import AgentState, create_initial_state
from ..agents.faculty_scraper import FacultyScraperAgent
from ..agents.research_enrichment import ResearchEnrichmentAgent
from ..agents.cv_parser import CVParserAgent
from ..agents.personalization import PersonalizationAgent
from ..utils.logger import get_logger
from ..utils.department_recommender import get_department_filters, recommend_departments

logger = get_logger(__name__)


# === Node Functions ===

async def scrape_faculty_node(state: AgentState) -> Dict[str, Any]:
    """
    Node 1: Scrape faculty profiles from IIT KGP website.
    
    If a CV is already parsed, uses CV skills to recommend relevant departments.
    
    Reads: faculty_url, target_departments, faculty_limit, student_cv
    Writes: faculty_profiles, logs, current_step, completed_steps
    """
    logger.info("Executing: scrape_faculty_node")
    
    # Get target departments - either provided or inferred from CV
    target_departments = state.get("target_departments")
    student_cv = state.get("student_cv")
    
    # If CV is parsed but no departments specified, recommend based on CV
    if not target_departments and student_cv:
        recommended_depts = recommend_departments(student_cv)
        target_departments = get_department_filters(student_cv)
        logger.info(f"Auto-detected departments from CV: {recommended_depts}")
    
    try:
        agent = FacultyScraperAgent()
        profiles = await agent.run(
            departments=target_departments,
            limit=state.get("faculty_limit"),
            save_to_file=True
        )
        
        dept_info = f" (departments: {target_departments})" if target_departments else ""
        
        return {
            "faculty_profiles": profiles,
            "logs": [f"Scraped {len(profiles)} faculty profiles{dept_info}"],
            "current_step": "faculty_scraped",
            "completed_steps": state.get("completed_steps", []) + ["scrape_faculty"]
        }
        
    except Exception as e:
        logger.error(f"Faculty scraping failed: {e}")
        return {
            "errors": [f"Faculty scraping failed: {str(e)}"],
            "current_step": "scrape_faculty_failed",
            "faculty_profiles": []
        }


async def enrich_profiles_node(state: AgentState) -> Dict[str, Any]:
    """
    Node 2: Enrich faculty profiles with research data.
    
    Reads: faculty_profiles
    Writes: enriched_profiles, logs, current_step, completed_steps
    """
    logger.info("Executing: enrich_profiles_node")
    
    profiles = state.get("faculty_profiles", [])
    
    if not profiles:
        return {
            "errors": ["No faculty profiles to enrich"],
            "current_step": "enrich_skipped",
            "enriched_profiles": []
        }
    
    try:
        agent = ResearchEnrichmentAgent()
        enriched = await agent.run(profiles, save_to_file=True)
        
        return {
            "enriched_profiles": enriched,
            "logs": [f"Enriched {len(enriched)} profiles"],
            "current_step": "profiles_enriched",
            "completed_steps": state.get("completed_steps", []) + ["enrich_profiles"]
        }
        
    except Exception as e:
        logger.error(f"Profile enrichment failed: {e}")
        # Fall back to basic profiles without enrichment
        from ..schemas.research import EnrichedProfile
        basic_enriched = [
            EnrichedProfile.from_faculty_profile(p) for p in profiles
        ]
        return {
            "enriched_profiles": basic_enriched,
            "errors": [f"Enrichment partially failed: {str(e)}"],
            "current_step": "enrich_fallback"
        }


async def parse_cv_node(state: AgentState) -> Dict[str, Any]:
    """
    Node 3: Parse student CV file.
    
    Reads: cv_path
    Writes: student_cv, logs, current_step, completed_steps
    """
    logger.info("Executing: parse_cv_node")
    
    cv_path = state.get("cv_path")
    
    if not cv_path:
        return {
            "errors": ["No CV path provided"],
            "current_step": "cv_parse_skipped",
            "student_cv": None
        }
    
    try:
        agent = CVParserAgent()
        student_cv = await agent.run(cv_path)
        
        return {
            "student_cv": student_cv,
            "logs": [f"Parsed CV for {student_cv.student_name}"],
            "current_step": "cv_parsed",
            "completed_steps": state.get("completed_steps", []) + ["parse_cv"]
        }
        
    except Exception as e:
        logger.error(f"CV parsing failed: {e}")
        return {
            "errors": [f"CV parsing failed: {str(e)}"],
            "current_step": "cv_parse_failed",
            "student_cv": None
        }


async def generate_emails_node(state: AgentState) -> Dict[str, Any]:
    """
    Node 4: Generate personalized emails and cover letters.
    
    Reads: enriched_profiles, student_cv, min_match_score
    Writes: email_outputs, logs, current_step, completed_steps
    """
    logger.info("Executing: generate_emails_node")
    
    enriched_profiles = state.get("enriched_profiles", [])
    student_cv = state.get("student_cv")
    min_score = state.get("min_match_score", 0.3)
    
    if not enriched_profiles:
        return {
            "errors": ["No enriched profiles available"],
            "current_step": "email_gen_skipped",
            "email_outputs": []
        }
    
    if not student_cv:
        return {
            "errors": ["No student CV available"],
            "current_step": "email_gen_skipped",
            "email_outputs": []
        }
    
    try:
        agent = PersonalizationAgent()
        outputs = await agent.run(
            student=student_cv,
            professors=enriched_profiles,
            min_match_score=min_score
        )
        
        return {
            "email_outputs": outputs,
            "logs": [f"Generated {len(outputs)} personalized emails"],
            "current_step": "emails_generated",
            "completed_steps": state.get("completed_steps", []) + ["generate_emails"]
        }
        
    except Exception as e:
        logger.error(f"Email generation failed: {e}")
        return {
            "errors": [f"Email generation failed: {str(e)}"],
            "current_step": "email_gen_failed",
            "email_outputs": []
        }


# === Conditional Edges ===

def should_generate_emails(state: AgentState) -> str:
    """
    Decide whether to proceed with email generation.
    
    Returns "generate" if both CV and profiles are available,
    otherwise returns "end".
    """
    has_profiles = len(state.get("enriched_profiles", [])) > 0
    has_cv = state.get("student_cv") is not None
    
    if has_profiles and has_cv:
        return "generate"
    return "end"


# === Workflow Creation ===

def create_workflow() -> StateGraph:
    """
    Create the LangGraph workflow for the agent pipeline.
    
    Graph Structure:
    
    [START] --> scrape_faculty --> enrich_profiles --+
                                                     |
    [START] --> parse_cv ----------------------------|
                                                     v
                                              generate_emails --> [END]
    
    Returns:
        Compiled StateGraph
    """
    workflow = StateGraph(AgentState)
    
    # Add nodes
    workflow.add_node("scrape_faculty", scrape_faculty_node)
    workflow.add_node("enrich_profiles", enrich_profiles_node)
    workflow.add_node("parse_cv", parse_cv_node)
    workflow.add_node("generate_emails", generate_emails_node)
    
    # Define edges
    # Main path: scrape -> enrich -> (conditional) -> generate
    workflow.set_entry_point("scrape_faculty")
    workflow.add_edge("scrape_faculty", "enrich_profiles")
    
    # After enrichment, check if we should generate emails
    workflow.add_conditional_edges(
        "enrich_profiles",
        should_generate_emails,
        {
            "generate": "generate_emails",
            "end": END
        }
    )
    
    workflow.add_edge("generate_emails", END)
    
    return workflow.compile()


def create_cv_only_workflow() -> StateGraph:
    """
    Create a workflow that only parses a CV.
    
    Useful for testing CV parsing independently.
    """
    workflow = StateGraph(AgentState)
    workflow.add_node("parse_cv", parse_cv_node)
    workflow.set_entry_point("parse_cv")
    workflow.add_edge("parse_cv", END)
    return workflow.compile()


def create_scrape_only_workflow() -> StateGraph:
    """
    Create a workflow that only scrapes faculty.
    
    Useful for collecting data without enrichment.
    """
    workflow = StateGraph(AgentState)
    workflow.add_node("scrape_faculty", scrape_faculty_node)
    workflow.set_entry_point("scrape_faculty")
    workflow.add_edge("scrape_faculty", END)
    return workflow.compile()


# === Pipeline Execution ===

async def run_pipeline(
    cv_path: Optional[str] = None,
    target_departments: Optional[List[str]] = None,
    faculty_limit: Optional[int] = None,
    min_match_score: float = 0.3,
    workflow_type: str = "full"
) -> AgentState:
    """
    Execute the full agent pipeline.
    
    Args:
        cv_path: Path to student CV file
        target_departments: List of departments to filter (None = all)
        faculty_limit: Maximum number of faculty to scrape
        min_match_score: Minimum match score for email generation
        workflow_type: "full", "scrape_only", or "cv_only"
        
    Returns:
        Final AgentState with all outputs
    """
    # Create initial state
    initial_state = create_initial_state(
        cv_path=cv_path,
        target_departments=target_departments,
        faculty_limit=faculty_limit,
        min_match_score=min_match_score
    )
    
    # Select and create workflow
    if workflow_type == "scrape_only":
        workflow = create_scrape_only_workflow()
    elif workflow_type == "cv_only":
        workflow = create_cv_only_workflow()
    else:
        workflow = create_workflow()
    
    # Run the workflow
    logger.info(f"Starting pipeline execution: {workflow_type}")
    
    # For full workflow, we need to handle CV parsing in parallel
    if workflow_type == "full" and cv_path:
        # Parse CV first (it's independent)
        cv_result = await parse_cv_node(initial_state)
        initial_state.update(cv_result)
    
    # Run main workflow
    final_state = await workflow.ainvoke(initial_state)
    
    logger.info(
        f"Pipeline complete. "
        f"Steps: {final_state.get('completed_steps', [])}. "
        f"Errors: {len(final_state.get('errors', []))}"
    )
    
    return final_state
