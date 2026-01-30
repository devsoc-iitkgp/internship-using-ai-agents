"""
Agent 3: CV Parsing Agent

Responsible for extracting structured data from student CVs.
"""

import json
from pathlib import Path
from typing import Optional, Union

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

from ..tools.document_parser import DocumentParser
from ..schemas.cv import (
    StudentCV, Education, Project, ResearchExperience,
    Internship, Competition, Skills, Coursework, Extracurriculars
)
from ..utils.config import settings
from ..utils.logger import AgentLogger


CV_EXTRACTION_PROMPT = """You are an expert CV parser for IIT Kharagpur student CVs. Extract structured information from the following CV text.

This CV follows the standard IIT KGP format with these sections:
- Header (Name, Roll Number, Department)
- EDUCATION (Year, Degree, Institute, CGPA/Marks)
- INTERNSHIPS (Company, Duration, Objectives, Bullet points)
- COMPETITION/CONFERENCE (Name, Duration, Objectives, Bullet points)
- PROJECTS (Name, Duration, Objectives, Bullet points)
- AWARDS AND ACHIEVEMENTS
- SKILLS AND EXPERTISE (Skills, Languages, Libraries/Frameworks, Tools/IDEs)
- COURSEWORK INFORMATION (Academic Courses, MOOCs)
- EXTRA CURRICULAR ACTIVITIES

CV TEXT:
{cv_text}

Extract the following and return as a valid JSON object:

{{
    "student_name": "Full name from header",
    "roll_number": "Roll number (e.g., 23CH10030)",
    "department": "Department from header (e.g., Chemical Engineering)",
    "email": "Email if found, or null",
    "phone": "Phone if found, or null",
    "education": [
        {{
            "degree": "Degree name (B.Tech, M.Tech, CBSE XII, etc.)",
            "institution": "Institution name",
            "field": "Field of study if mentioned",
            "year": "Year of completion or expected",
            "gpa": "CGPA or percentage"
        }}
    ],
    "internships": [
        {{
            "title": "Role/Position",
            "organization": "Company/Institute name",
            "duration": "Duration (e.g., Sep '24 - Nov '24)",
            "objective": "Main objective from CV",
            "highlights": ["Key bullet points/achievements"]
        }}
    ],
    "competitions": [
        {{
            "name": "Competition/Conference name",
            "achievement": "Medal/Prize (Gold, Silver, etc.)",
            "duration": "Duration",
            "objective": "Main objective",
            "highlights": ["Key achievements"]
        }}
    ],
    "projects": [
        {{
            "title": "Project name",
            "type": "Self-project, Course project, etc.",
            "duration": "Duration",
            "objective": "Main objective",
            "technologies": ["Technologies used"],
            "highlights": ["Key achievements"],
            "link": "GitHub/Demo link if available"
        }}
    ],
    "skills": {{
        "core_skills": ["Competitive Programming", "ML", "Web Dev", etc.],
        "programming_languages": ["C++", "Python", etc.],
        "frameworks": ["React.js", "PyTorch", etc.],
        "tools": ["Docker", "AWS", etc.]
    }},
    "achievements": ["List of awards and achievements"],
    "coursework": {{
        "academic": ["List of academic courses"],
        "moocs": ["List of MOOCs/certifications"]
    }},
    "extracurriculars": {{
        "social_cultural": ["Street Play, Films, etc."],
        "clubs_societies": ["Club memberships"]
    }},
    "interests": ["Research interests inferred from projects/internships"]
}}

Important:
1. Extract information EXACTLY as stated in the CV
2. Do not make up or assume information
3. Parse all bullet points as highlights arrays
4. Extract links where available
5. Identify the department from header (e.g., "B.Tech.(Hons.) in CHEMICAL ENGINEERING" -> "Chemical Engineering")
6. Return ONLY valid JSON, no additional text

JSON Output:"""


class CVParserAgent:
    """
    CV Parsing Agent - Agent 3 in the pipeline.
    
    Parses and extracts structured data from IIT KGP student CVs.
    
    Responsibilities:
    - Parse PDF/DOCX files to extract text
    - Use LLM for structured information extraction
    - Normalize skill taxonomy
    - Validate output against IIT KGP CV schema
    """
    
    def __init__(self, api_key: Optional[str] = None):
        self.logger = AgentLogger("CVParserAgent")
        self.document_parser = DocumentParser()
        self.llm = ChatOpenAI(
            model=settings.llm_model,
            temperature=0.1,  # Low temperature for accurate extraction
            api_key=api_key or settings.openai_api_key
        )
    
    async def run(self, file_path: Union[str, Path]) -> StudentCV:
        """
        Parse a CV file and extract structured data.
        
        Args:
            file_path: Path to PDF or DOCX file
            
        Returns:
            StudentCV object with extracted data
        """
        self.logger.info("Parsing CV", path=str(file_path))
        
        # Extract text from document
        text = self.document_parser.parse(file_path)
        self.logger.info(f"Extracted {len(text)} characters from document")
        
        # Extract structured data using LLM
        cv_data = await self._extract_cv_data(text)
        
        # Normalize skills
        cv_data = self._normalize_skills(cv_data)
        
        # Validate and create StudentCV object
        student_cv = self._validate_and_create(cv_data)
        
        self.logger.info("CV parsing complete", name=student_cv.student_name)
        
        return student_cv
    
    async def run_from_bytes(
        self, 
        content: bytes, 
        filename: str
    ) -> StudentCV:
        """
        Parse CV from file bytes (for API uploads).
        
        Args:
            content: Raw file bytes
            filename: Original filename
            
        Returns:
            StudentCV object with extracted data
        """
        self.logger.info("Parsing CV from bytes", filename=filename)
        
        text = self.document_parser.parse_bytes(content, filename)
        cv_data = await self._extract_cv_data(text)
        cv_data = self._normalize_skills(cv_data)
        
        return self._validate_and_create(cv_data)
    
    async def _extract_cv_data(self, text: str) -> dict:
        """Extract structured data from CV text using LLM."""
        # Truncate very long CVs
        max_length = 8000
        if len(text) > max_length:
            text = text[:max_length] + "\n[... truncated ...]"
        
        prompt = ChatPromptTemplate.from_template(CV_EXTRACTION_PROMPT)
        message = prompt.format_messages(cv_text=text)
        
        try:
            response = await self.llm.ainvoke(message)
            content = response.content.strip()
            
            # Handle potential markdown code blocks
            if content.startswith("```"):
                content = content.split("```")[1]
                if content.startswith("json"):
                    content = content[4:]
            
            cv_data = json.loads(content)
            return cv_data
            
        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse LLM response as JSON: {e}")
            # Return minimal valid structure
            return {
                "student_name": "Unknown",
                "education": [],
                "internships": [],
                "competitions": [],
                "projects": [],
                "skills": {"core_skills": [], "programming_languages": [], "frameworks": [], "tools": []},
                "achievements": [],
                "coursework": {"academic": [], "moocs": []},
                "extracurriculars": {"social_cultural": [], "clubs_societies": []},
                "interests": []
            }
    
    def _normalize_skills(self, cv_data: dict) -> dict:
        """Normalize skill names to standard taxonomy."""
        skill_mapping = {
            "ml": "Machine Learning",
            "dl": "Deep Learning",
            "ai": "Artificial Intelligence",
            "nlp": "Natural Language Processing",
            "cv": "Computer Vision",
            "js": "JavaScript",
            "ts": "TypeScript",
            "py": "Python",
            "cpp": "C++",
            "tf": "TensorFlow",
            "pytorch": "PyTorch",
            "aws": "Amazon Web Services",
            "gcp": "Google Cloud Platform",
            "k8s": "Kubernetes",
            "sql": "SQL",
            "nosql": "NoSQL",
            "dsa": "Data Structures and Algorithms",
            "oops": "Object Oriented Programming",
            "mlops": "MLOps",
        }
        
        skills_data = cv_data.get("skills", {})
        
        # Handle both old (list) and new (dict) format
        if isinstance(skills_data, list):
            # Old format - convert to new
            normalized = []
            for skill in skills_data:
                skill_lower = skill.lower().strip()
                if skill_lower in skill_mapping:
                    normalized.append(skill_mapping[skill_lower])
                else:
                    normalized.append(skill.strip())
            cv_data["skills"] = {
                "core_skills": list(set(normalized)),
                "programming_languages": [],
                "frameworks": [],
                "tools": []
            }
        elif isinstance(skills_data, dict):
            # New IIT KGP format - normalize each category
            for category in ["core_skills", "programming_languages", "frameworks", "tools"]:
                skills_list = skills_data.get(category, [])
                normalized = []
                for skill in skills_list:
                    if isinstance(skill, str):
                        skill_lower = skill.lower().strip()
                        if skill_lower in skill_mapping:
                            normalized.append(skill_mapping[skill_lower])
                        else:
                            normalized.append(skill.strip())
                cv_data["skills"][category] = list(set(normalized))
        
        return cv_data
    
    def _validate_and_create(self, cv_data: dict) -> StudentCV:
        """Validate data and create StudentCV object for IIT KGP format."""
        
        # Process education
        education = []
        for edu in cv_data.get("education", []):
            if isinstance(edu, dict) and edu.get("degree"):
                education.append(Education(**edu))
        
        # Process internships
        internships = []
        for intern in cv_data.get("internships", []):
            if isinstance(intern, dict) and intern.get("title"):
                internships.append(Internship(**intern))
        
        # Process competitions
        competitions = []
        for comp in cv_data.get("competitions", []):
            if isinstance(comp, dict) and comp.get("name"):
                competitions.append(Competition(**comp))
        
        # Process projects
        projects = []
        for proj in cv_data.get("projects", []):
            if isinstance(proj, dict) and proj.get("title"):
                projects.append(Project(**proj))
        
        # Process skills
        skills_data = cv_data.get("skills", {})
        if isinstance(skills_data, dict):
            skills = Skills(**skills_data)
        else:
            skills = Skills(core_skills=skills_data if isinstance(skills_data, list) else [])
        
        # Process coursework
        coursework_data = cv_data.get("coursework", {})
        coursework = Coursework(**coursework_data) if isinstance(coursework_data, dict) else Coursework()
        
        # Process extracurriculars
        extra_data = cv_data.get("extracurriculars", {})
        extracurriculars = Extracurriculars(**extra_data) if isinstance(extra_data, dict) else Extracurriculars()
        
        # Build flat skills list for matching compatibility
        skills_list = skills.core_skills + skills.programming_languages + skills.frameworks + skills.tools
        
        return StudentCV(
            student_name=cv_data.get("student_name", "Unknown"),
            roll_number=cv_data.get("roll_number"),
            department=cv_data.get("department"),
            email=cv_data.get("email"),
            phone=cv_data.get("phone"),
            education=education,
            internships=internships,
            competitions=competitions,
            projects=projects,
            skills=skills,
            skills_list=list(set(skills_list)),
            achievements=cv_data.get("achievements", []),
            coursework=coursework,
            extracurriculars=extracurriculars,
            interests=cv_data.get("interests", []),
            publications=cv_data.get("publications", []),
            research_experience=[]  # Can be populated from internships if needed
        )

