"""Student CV schema for Agent 3 (CV Parser) - IIT Kharagpur Format."""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict


class Education(BaseModel):
    """Educational qualification entry."""
    
    degree: str = Field(..., description="Degree name (B.Tech, M.Tech, CBSE XII, etc.)")
    institution: str = Field(..., description="Institution name")
    field: Optional[str] = Field(None, description="Field of study")
    year: Optional[str] = Field(None, description="Year of completion or expected")
    gpa: Optional[str] = Field(None, description="CGPA or percentage")


class Internship(BaseModel):
    """Internship experience entry - IIT KGP format."""
    
    title: str = Field(..., description="Role/Position")
    organization: str = Field(..., description="Company/Institute name")
    duration: Optional[str] = Field(None, description="Duration (e.g., Sep '24 - Nov '24)")
    objective: Optional[str] = Field(None, description="Main objective")
    highlights: List[str] = Field(default_factory=list, description="Key achievements/bullet points")


class Competition(BaseModel):
    """Competition/Conference entry - IIT KGP format."""
    
    name: str = Field(..., description="Competition/Conference name")
    achievement: Optional[str] = Field(None, description="Medal/Prize (Gold, Silver, etc.)")
    duration: Optional[str] = Field(None, description="Duration")
    objective: Optional[str] = Field(None, description="Main objective")
    highlights: List[str] = Field(default_factory=list, description="Key achievements")


class Project(BaseModel):
    """Project entry - IIT KGP format."""
    
    title: str = Field(..., description="Project name")
    type: Optional[str] = Field(None, description="Self-project, Course project, etc.")
    duration: Optional[str] = Field(None, description="Duration")
    objective: Optional[str] = Field(None, description="Main objective")
    technologies: List[str] = Field(default_factory=list, description="Technologies used")
    highlights: List[str] = Field(default_factory=list, description="Key achievements")
    link: Optional[str] = Field(None, description="GitHub/Demo link")


class Skills(BaseModel):
    """Structured skills - IIT KGP format."""
    
    core_skills: List[str] = Field(default_factory=list, description="Core competencies")
    programming_languages: List[str] = Field(default_factory=list, description="Programming languages")
    frameworks: List[str] = Field(default_factory=list, description="Libraries and frameworks")
    tools: List[str] = Field(default_factory=list, description="Tools and IDEs")


class Coursework(BaseModel):
    """Coursework information - IIT KGP format."""
    
    academic: List[str] = Field(default_factory=list, description="Academic courses")
    moocs: List[str] = Field(default_factory=list, description="MOOCs and certifications")


class Extracurriculars(BaseModel):
    """Extracurricular activities - IIT KGP format."""
    
    social_cultural: List[str] = Field(default_factory=list, description="Social and cultural activities")
    clubs_societies: List[str] = Field(default_factory=list, description="Club memberships")


class ResearchExperience(BaseModel):
    """Research experience entry (legacy support)."""
    
    title: str = Field(..., description="Research title or position")
    organization: Optional[str] = Field(None, description="Lab, university, or organization")
    description: str = Field("", description="Description of research work")
    duration: Optional[str] = Field(None, description="Duration of research")
    supervisor: Optional[str] = Field(None, description="Research supervisor name")


class StudentCV(BaseModel):
    """
    Structured representation of an IIT Kharagpur student's CV.
    
    This schema is designed for the standard IIT KGP CV format used for
    internship and placement applications.
    """
    
    # Header Information
    student_name: str = Field(..., description="Full name of the student")
    roll_number: Optional[str] = Field(None, description="IIT KGP Roll Number")
    department: Optional[str] = Field(None, description="Department name")
    email: Optional[str] = Field(None, description="Student email")
    phone: Optional[str] = Field(None, description="Student phone number")
    
    # Education Section
    education: List[Education] = Field(
        default_factory=list, 
        description="Educational qualifications"
    )
    
    # Experience Sections
    internships: List[Internship] = Field(
        default_factory=list,
        description="Internship experiences"
    )
    competitions: List[Competition] = Field(
        default_factory=list,
        description="Competitions and conferences"
    )
    projects: List[Project] = Field(
        default_factory=list, 
        description="Academic and personal projects"
    )
    
    # Skills Section
    skills: Skills = Field(
        default_factory=Skills,
        description="Technical and research skills"
    )
    
    # Legacy: Flat skills list for compatibility
    skills_list: List[str] = Field(
        default_factory=list,
        description="Flattened skills list for matching"
    )
    
    # Research (for research internships)
    research_experience: List[ResearchExperience] = Field(
        default_factory=list, 
        description="Research experience entries"
    )
    
    # Achievements and Awards
    achievements: List[str] = Field(
        default_factory=list, 
        description="Awards, honors, achievements"
    )
    
    # Coursework
    coursework: Coursework = Field(
        default_factory=Coursework,
        description="Academic courses and MOOCs"
    )
    
    # Extracurriculars
    extracurriculars: Extracurriculars = Field(
        default_factory=Extracurriculars,
        description="Extracurricular activities"
    )
    
    # Research Interests
    interests: List[str] = Field(
        default_factory=list, 
        description="Research/academic interests"
    )
    
    # For backward compatibility
    publications: List[str] = Field(
        default_factory=list, 
        description="Publications (if any)"
    )
    
    def get_all_skills(self) -> List[str]:
        """Get all skills as a flat list for matching."""
        all_skills = []
        if self.skills:
            all_skills.extend(self.skills.core_skills)
            all_skills.extend(self.skills.programming_languages)
            all_skills.extend(self.skills.frameworks)
            all_skills.extend(self.skills.tools)
        all_skills.extend(self.skills_list)
        return list(set(all_skills))
    
    def get_project_technologies(self) -> List[str]:
        """Get all technologies from projects."""
        techs = []
        for project in self.projects:
            techs.extend(project.technologies)
        return list(set(techs))
    
    class Config:
        json_schema_extra = {
            "example": {
                "student_name": "Harsh Bhatt",
                "roll_number": "23CH10030",
                "department": "Chemical Engineering",
                "education": [
                    {
                        "degree": "B.Tech",
                        "institution": "IIT Kharagpur",
                        "field": "Chemical Engineering",
                        "year": "2027",
                        "gpa": "8.63/10"
                    }
                ],
                "internships": [
                    {
                        "title": "Full Stack Developer Intern",
                        "organization": "wiZe",
                        "duration": "Sep '24 - Nov '24",
                        "objective": "Built AI-powered career platform",
                        "highlights": ["Built frontend with Next.js", "Reduced re-renders by 15%"]
                    }
                ],
                "competitions": [
                    {
                        "name": "Inter IIT Tech Meet 13.0",
                        "achievement": "Gold",
                        "objective": "Fantasy Points Prediction",
                        "highlights": ["Engineered 50+ features"]
                    }
                ],
                "projects": [
                    {
                        "title": "DeepFake Detection Platform",
                        "type": "Self-project",
                        "technologies": ["React.js", "XceptionNet", "Solidity"],
                        "link": "https://scan-x.vercel.app"
                    }
                ],
                "skills": {
                    "core_skills": ["Machine Learning", "Web Development"],
                    "programming_languages": ["Python", "C++", "JavaScript"],
                    "frameworks": ["React.js", "PyTorch", "Next.js"],
                    "tools": ["Docker", "AWS", "Git"]
                },
                "interests": ["Deep Learning", "Quantum Computing", "Blockchain"]
            }
        }
