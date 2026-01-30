"""FastAPI REST API for the Internship Agent System."""

from fastapi import FastAPI, HTTPException, UploadFile, File, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import json
import uuid
from pathlib import Path
from datetime import datetime

from src.agents.faculty_scraper import FacultyScraperAgent
from src.agents.research_enrichment import ResearchEnrichmentAgent
from src.agents.cv_parser import CVParserAgent
from src.agents.personalization import PersonalizationAgent
from src.schemas.faculty import FacultyProfile
from src.schemas.research import EnrichedProfile
from src.schemas.cv import StudentCV
from src.schemas.output import EmailOutput
from src.graph.workflow import run_pipeline
from src.utils.config import settings
from src.utils.logger import get_logger

logger = get_logger(__name__)

app = FastAPI(
    title="Internship Agent System",
    description="Multi-agent system for automated internship outreach to IIT Kharagpur professors",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory job store (use Redis/DB in production)
jobs: Dict[str, Dict[str, Any]] = {}


# === Request/Response Models ===

class ScrapeRequest(BaseModel):
    departments: Optional[List[str]] = Field(
        None, 
        description="List of department names to filter"
    )
    limit: Optional[int] = Field(
        None, 
        description="Maximum number of faculty to scrape"
    )


class EnrichRequest(BaseModel):
    faculty_profiles: List[Dict[str, Any]] = Field(
        ..., 
        description="List of faculty profiles to enrich"
    )


class GenerateRequest(BaseModel):
    student_cv: Dict[str, Any] = Field(
        ..., 
        description="Parsed student CV data"
    )
    professor_profiles: List[Dict[str, Any]] = Field(
        ..., 
        description="Enriched professor profiles"
    )
    min_match_score: float = Field(
        0.3, 
        description="Minimum match score for email generation"
    )


class BatchRequest(BaseModel):
    cv_path: Optional[str] = Field(
        None, 
        description="Path to student CV file"
    )
    departments: Optional[List[str]] = Field(
        None, 
        description="List of departments to filter"
    )
    faculty_limit: Optional[int] = Field(
        None, 
        description="Maximum faculty to process"
    )
    min_match_score: float = Field(
        0.3,
        description="Minimum match score"
    )


class JobStatus(BaseModel):
    job_id: str
    status: str
    progress: Optional[str] = None
    result: Optional[Dict[str, Any]] = None
    errors: Optional[List[str]] = None
    created_at: str
    completed_at: Optional[str] = None


# === API Endpoints ===

@app.get("/")
async def root():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "Internship Agent System",
        "version": "1.0.0"
    }


@app.post("/scrape", response_model=List[Dict[str, Any]])
async def scrape_faculty(request: ScrapeRequest):
    """
    Scrape faculty profiles from IIT KGP website.
    
    This is a synchronous endpoint - use /batch for async processing.
    """
    try:
        agent = FacultyScraperAgent()
        profiles = await agent.run(
            departments=request.departments,
            limit=request.limit,
            save_to_file=True
        )
        return [p.model_dump() for p in profiles]
        
    except Exception as e:
        logger.error(f"Scrape failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/faculty", response_model=List[Dict[str, Any]])
async def get_faculty():
    """Get previously scraped faculty profiles."""
    try:
        profiles = FacultyScraperAgent.load_profiles()
        return [p.model_dump() for p in profiles]
    except Exception as e:
        logger.error(f"Load failed: {e}")
        return []


@app.post("/enrich", response_model=List[Dict[str, Any]])
async def enrich_profiles(request: EnrichRequest):
    """
    Enrich faculty profiles with research data.
    """
    try:
        profiles = [FacultyProfile(**p) for p in request.faculty_profiles]
        agent = ResearchEnrichmentAgent()
        enriched = await agent.run(profiles, save_to_file=True)
        return [p.model_dump() for p in enriched]
        
    except Exception as e:
        logger.error(f"Enrich failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/enriched", response_model=List[Dict[str, Any]])
async def get_enriched():
    """Get previously enriched profiles."""
    try:
        profiles = ResearchEnrichmentAgent.load_profiles()
        return [p.model_dump() for p in profiles]
    except Exception as e:
        logger.error(f"Load failed: {e}")
        return []


@app.post("/cv/upload", response_model=Dict[str, Any])
async def upload_cv(file: UploadFile = File(...)):
    """
    Upload and parse a student CV (PDF or DOCX).
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")
    
    # Validate file type
    allowed_extensions = [".pdf", ".docx", ".doc"]
    extension = Path(file.filename).suffix.lower()
    if extension not in allowed_extensions:
        raise HTTPException(
            status_code=400, 
            detail=f"Unsupported file type. Allowed: {allowed_extensions}"
        )
    
    try:
        content = await file.read()
        agent = CVParserAgent()
        student_cv = await agent.run_from_bytes(content, file.filename)
        return student_cv.model_dump()
        
    except Exception as e:
        logger.error(f"CV parsing failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/cv/parse", response_model=Dict[str, Any])
async def parse_cv_from_path(cv_path: str):
    """
    Parse a CV from a local file path.
    """
    path = Path(cv_path)
    if not path.exists():
        raise HTTPException(status_code=404, detail=f"File not found: {cv_path}")
    
    try:
        agent = CVParserAgent()
        student_cv = await agent.run(cv_path)
        return student_cv.model_dump()
        
    except Exception as e:
        logger.error(f"CV parsing failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/generate", response_model=List[Dict[str, Any]])
async def generate_emails(request: GenerateRequest):
    """
    Generate personalized emails for matching professors.
    """
    try:
        student = StudentCV(**request.student_cv)
        professors = [EnrichedProfile(**p) for p in request.professor_profiles]
        
        agent = PersonalizationAgent()
        outputs = await agent.run(
            student=student,
            professors=professors,
            min_match_score=request.min_match_score
        )
        
        return [o.model_dump() for o in outputs]
        
    except Exception as e:
        logger.error(f"Generation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/batch", response_model=JobStatus)
async def start_batch_pipeline(
    request: BatchRequest,
    background_tasks: BackgroundTasks
):
    """
    Start a batch processing job for the full pipeline.
    
    Returns a job ID for tracking progress.
    """
    job_id = str(uuid.uuid4())
    
    jobs[job_id] = {
        "status": "started",
        "progress": "Initializing pipeline",
        "created_at": datetime.now().isoformat(),
        "errors": []
    }
    
    # Add to background tasks
    background_tasks.add_task(
        run_batch_pipeline,
        job_id,
        request.cv_path,
        request.departments,
        request.faculty_limit,
        request.min_match_score
    )
    
    return JobStatus(
        job_id=job_id,
        status="started",
        progress="Initializing pipeline",
        created_at=jobs[job_id]["created_at"]
    )


async def run_batch_pipeline(
    job_id: str,
    cv_path: Optional[str],
    departments: Optional[List[str]],
    faculty_limit: Optional[int],
    min_match_score: float
):
    """Background task to run the full pipeline."""
    try:
        jobs[job_id]["progress"] = "Running pipeline"
        
        final_state = await run_pipeline(
            cv_path=cv_path,
            target_departments=departments,
            faculty_limit=faculty_limit,
            min_match_score=min_match_score
        )
        
        jobs[job_id].update({
            "status": "completed",
            "progress": "Pipeline completed",
            "completed_at": datetime.now().isoformat(),
            "result": {
                "faculty_count": len(final_state.get("faculty_profiles", [])),
                "enriched_count": len(final_state.get("enriched_profiles", [])),
                "email_count": len(final_state.get("email_outputs", [])),
                "completed_steps": final_state.get("completed_steps", []),
                "email_outputs": [
                    o.model_dump() for o in final_state.get("email_outputs", [])
                ]
            },
            "errors": final_state.get("errors", [])
        })
        
    except Exception as e:
        logger.error(f"Batch pipeline failed: {e}")
        jobs[job_id].update({
            "status": "failed",
            "progress": f"Failed: {str(e)}",
            "completed_at": datetime.now().isoformat(),
            "errors": [str(e)]
        })


@app.get("/status/{job_id}", response_model=JobStatus)
async def get_job_status(job_id: str):
    """Get the status of a batch processing job."""
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job = jobs[job_id]
    return JobStatus(
        job_id=job_id,
        status=job.get("status", "unknown"),
        progress=job.get("progress"),
        result=job.get("result"),
        errors=job.get("errors"),
        created_at=job.get("created_at", ""),
        completed_at=job.get("completed_at")
    )


@app.get("/jobs", response_model=List[JobStatus])
async def list_jobs():
    """List all jobs and their statuses."""
    return [
        JobStatus(
            job_id=job_id,
            status=job.get("status", "unknown"),
            progress=job.get("progress"),
            result=job.get("result"),
            errors=job.get("errors"),
            created_at=job.get("created_at", ""),
            completed_at=job.get("completed_at")
        )
        for job_id, job in jobs.items()
    ]


# === Startup/Shutdown ===

@app.on_event("startup")
async def startup_event():
    """Initialize directories on startup."""
    settings.ensure_directories()
    logger.info("Internship Agent System API started")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
