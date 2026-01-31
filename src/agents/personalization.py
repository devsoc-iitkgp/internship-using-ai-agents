"""
Agent 4: Personalization & Writing Agent

Responsible for generating personalized cold emails and cover letters.
"""

import json
from datetime import datetime
from typing import List, Optional

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate

from ..schemas.cv import StudentCV
from ..schemas.research import EnrichedProfile
from ..schemas.output import EmailOutput, MatchReason
from ..utils.config import settings
from ..utils.logger import AgentLogger


MATCHING_PROMPT = """You are an expert at matching student profiles with professor research interests.

Analyze the overlap between the student's background and the professor's research.

PROFESSOR INFORMATION:
Name: {professor_name}
Department: {department}
Research Areas: {research_areas}
Expertise Keywords: {expertise_keywords}
Recent Publications: {publications}
Bio: {bio}

STUDENT INFORMATION:
Name: {student_name}
Skills: {skills}
Projects: {projects}
Research Experience: {research_experience}
Interests: {interests}

Find specific matches between:
1. Student skills and professor expertise keywords
2. Student projects and professor research areas
3. Student interests and professor's work

Return a JSON object with match analysis:
{{
    "matches": [
        {{
            "category": "skill|project|research_area",
            "student_item": "Specific item from student profile",
            "professor_item": "Related item from professor profile",
            "relevance_score": 0.0-1.0,
            "explanation": "Why this is a good match"
        }}
    ],
    "overall_score": 0.0-1.0,
    "key_talking_points": ["List of 2-3 key points to mention in email"]
}}

Be specific and accurate. Only include genuine matches, not forced ones.
JSON Output:"""


EMAIL_GENERATION_PROMPT = """You are an expert at writing professional, personalized cold emails for research internships.

Write a cold email from a student to a professor requesting a research internship opportunity.

PROFESSOR INFORMATION:
Name: {professor_name}
Department: {department}
Research Areas: {research_areas}
Recent Work: {recent_work}

STUDENT INFORMATION:
Name: {student_name}
Education: {education}
Key Skills: {skills}
Relevant Projects: {projects}

MATCHING ANALYSIS:
Key Matches: {key_matches}
Key Talking Points: {talking_points}

REQUIREMENTS:
1. Subject line: Short, specific, and professional (e.g., "Research Internship Inquiry - [Specific Area]")
2. Email body:
   - Professional greeting
   - Brief self-introduction (1 sentence)
   - Why you're interested in THEIR specific research (reference their work)
   - Your relevant qualifications (link to their needs)
   - Clear ask for internship opportunity
   - Professional closing
3. Tone: Formal but not stiff, confident but humble
4. Length: 150-200 words maximum
5. DO NOT make up any claims about yourself or the professor
6. DO NOT use generic phrases like "I am fascinated by your work"

Return a JSON object:
{{
    "email_subject": "Subject line",
    "email_body": "Full email body"
}}

JSON Output:"""


COVER_LETTER_PROMPT = """You are an expert at writing compelling research internship cover letters.

Write a cover letter for a research internship application.

PROFESSOR INFORMATION:
Name: Professor {professor_name}
Department: {department}
Institution: IIT Kharagpur
Research Focus: {research_areas}

STUDENT INFORMATION:
Name: {student_name}
Education: {education}
Skills: {skills}
Key Projects: {projects}
Research Experience: {research_experience}

MATCHING ANALYSIS:
Key Matches: {key_matches}

REQUIREMENTS:
1. Professional header and formatting
2. Strong opening that shows specific interest
3. Body paragraphs:
   - Your relevant academic background
   - Specific technical skills that align with their research
   - Relevant project or research experience
   - What you hope to contribute and learn
4. Professional closing with clear call to action
5. Maximum 1 page (300-350 words)
6. No generic statements - be specific
7. Do not make up any information

Return the complete cover letter text, not JSON. Use proper formatting with line breaks."""


class PersonalizationAgent:
    """
    Personalization & Writing Agent - Agent 4 in the pipeline.
    
    Generates personalized cold emails and cover letters.
    
    Responsibilities:
    - Identify overlap between student profile and professor research
    - Generate personalized cold emails
    - Generate custom cover letters
    - Ensure no hallucinated claims
    """
    
    def __init__(self, api_key: Optional[str] = None):
        self.logger = AgentLogger("PersonalizationAgent")
        self.llm = ChatGoogleGenerativeAI(
            model=settings.llm_model,
            temperature=settings.llm_temperature,
            google_api_key=api_key or settings.google_api_key
        )
    
    def _get_content_str(self, content) -> str:
        """Safely extract string from LLM response content.
        
        Gemini can return content as a list of parts instead of a string.
        This helper handles both cases.
        """
        if isinstance(content, list):
            # Join all text parts from the list
            return "".join(
                part.get("text", str(part)) if isinstance(part, dict) else str(part)
                for part in content
            )
        return str(content) if content else ""
    
    async def run(
        self,
        student: StudentCV,
        professors: List[EnrichedProfile],
        min_match_score: float = 0.3
    ) -> List[EmailOutput]:
        """
        Generate personalized outreach for multiple professors.
        
        Args:
            student: StudentCV with student information
            professors: List of EnrichedProfile objects
            min_match_score: Minimum match score to generate email
            
        Returns:
            List of EmailOutput objects
        """
        self.logger.info(
            f"Generating outreach for {len(professors)} professors",
            student=student.student_name
        )
        
        outputs: List[EmailOutput] = []
        
        for professor in professors:
            try:
                output = await self.generate_outreach(student, professor)
                
                if output.overall_match_score >= min_match_score:
                    outputs.append(output)
                    self.logger.info(
                        "Generated email",
                        professor=professor.name,
                        score=output.overall_match_score
                    )
                else:
                    self.logger.info(
                        "Skipped - low match score",
                        professor=professor.name,
                        score=output.overall_match_score
                    )
                    
            except Exception as e:
                self.logger.error(f"Failed to generate for {professor.name}: {e}")
        
        # Sort by match score
        outputs.sort(key=lambda x: x.overall_match_score, reverse=True)
        
        return outputs
    
    async def generate_outreach(
        self,
        student: StudentCV,
        professor: EnrichedProfile
    ) -> EmailOutput:
        """
        Generate personalized email and cover letter for a single professor.
        
        Args:
            student: StudentCV object
            professor: EnrichedProfile object
            
        Returns:
            EmailOutput with email and cover letter
        """
        # Step 1: Analyze matches
        match_analysis = await self._analyze_matches(student, professor)
        
        # Step 2: Generate email
        email_data = await self._generate_email(student, professor, match_analysis)
        
        # Step 3: Generate cover letter
        cover_letter = await self._generate_cover_letter(student, professor, match_analysis)
        
        # Build match reasons
        match_reasons = [
            MatchReason(**match) for match in match_analysis.get("matches", [])
        ]
        
        return EmailOutput(
            professor_name=professor.name,
            professor_email=professor.email,
            department=professor.department,
            profile_url=professor.profile_url,
            match_reasons=match_reasons,
            overall_match_score=match_analysis.get("overall_score", 0.0),
            email_subject=email_data.get("email_subject", "Research Internship Inquiry"),
            email_body=email_data.get("email_body", ""),
            cover_letter=cover_letter,
            generated_at=datetime.now().isoformat(),
            model_used=settings.llm_model
        )
    
    async def _analyze_matches(
        self,
        student: StudentCV,
        professor: EnrichedProfile
    ) -> dict:
        """Analyze matches between student and professor profiles."""
        prompt = ChatPromptTemplate.from_template(MATCHING_PROMPT)
        
        # Format projects for prompt
        projects_str = "\n".join([
            f"- {p.title}: {getattr(p, 'objective', '') or getattr(p, 'description', '')}" for p in student.projects[:5]
        ]) if student.projects else "None listed"
        
        # Format research experience
        research_str = "\n".join([
            f"- {r.title}: {r.description}" for r in student.research_experience[:3]
        ]) if student.research_experience else "None listed"
        
        # Format publications
        pubs_str = "\n".join([
            f"- {p.title}" for p in professor.recent_publications[:5]
        ]) if professor.recent_publications else "Not available"
        
        message = prompt.format_messages(
            professor_name=professor.name,
            department=professor.department,
            research_areas=", ".join(professor.research_areas) if professor.research_areas else "Not specified",
            expertise_keywords=", ".join(professor.expertise_keywords) if professor.expertise_keywords else "Not available",
            publications=pubs_str,
            bio=professor.bio[:1000] if professor.bio else "Not available",
            student_name=student.student_name,
            skills=", ".join(student.get_all_skills()[:15]) if student.get_all_skills() else "Not listed",
            projects=projects_str,
            research_experience=research_str,
            interests=", ".join(student.interests) if student.interests else "Not listed"
        )
        
        try:
            response = await self.llm.ainvoke(message)
            content = self._get_content_str(response.content).strip()
            
            # Handle markdown code blocks
            if "```" in content:
                content = content.split("```")[1]
                if content.startswith("json"):
                    content = content[4:]
            
            return json.loads(content)
            
        except Exception as e:
            self.logger.error(f"Match analysis failed: {e}")
            return {"matches": [], "overall_score": 0.0, "key_talking_points": []}
    
    async def _generate_email(
        self,
        student: StudentCV,
        professor: EnrichedProfile,
        match_analysis: dict
    ) -> dict:
        """Generate personalized email."""
        prompt = ChatPromptTemplate.from_template(EMAIL_GENERATION_PROMPT)
        
        # Format education
        education_str = ", ".join([
            f"{e.degree} in {e.field or 'N/A'} from {e.institution}"
            for e in student.education[:2]
        ]) if student.education else "Not specified"
        
        # Format projects
        projects_str = "\n".join([
            f"- {p.title}: {(getattr(p, 'objective', '') or getattr(p, 'description', ''))[:100]}" for p in student.projects[:3]
        ]) if student.projects else "None listed"
        
        # Recent work
        recent_work = professor.bio[:500] if professor.bio else (
            ", ".join(professor.research_areas) if professor.research_areas else "Not available"
        )
        
        # Key matches
        matches_str = "\n".join([
            f"- {m.get('student_item')} relates to {m.get('professor_item')}"
            for m in match_analysis.get("matches", [])[:3]
        ]) if match_analysis.get("matches") else "General interest in the field"
        
        message = prompt.format_messages(
            professor_name=professor.name,
            department=professor.department,
            research_areas=", ".join(professor.research_areas[:5]) if professor.research_areas else "their research",
            recent_work=recent_work,
            student_name=student.student_name,
            education=education_str,
            skills=", ".join(student.get_all_skills()[:10]) if student.get_all_skills() else "various technical skills",
            projects=projects_str,
            key_matches=matches_str,
            talking_points=", ".join(match_analysis.get("key_talking_points", []))
        )
        
        try:
            response = await self.llm.ainvoke(message)
            content = self._get_content_str(response.content).strip()
            
            if "```" in content:
                content = content.split("```")[1]
                if content.startswith("json"):
                    content = content[4:]
            
            return json.loads(content)
            
        except Exception as e:
            self.logger.error(f"Email generation failed: {e}")
            return {
                "email_subject": f"Research Internship Inquiry - {professor.department}",
                "email_body": f"Dear Professor {professor.name},\n\nI am writing to inquire about research internship opportunities in your lab.\n\nBest regards,\n{student.student_name}"
            }
    
    async def _generate_cover_letter(
        self,
        student: StudentCV,
        professor: EnrichedProfile,
        match_analysis: dict
    ) -> str:
        """Generate cover letter."""
        prompt = ChatPromptTemplate.from_template(COVER_LETTER_PROMPT)
        
        # Format all student info
        education_str = "\n".join([
            f"- {e.degree} in {e.field or 'N/A'} from {e.institution} ({e.year or 'N/A'})"
            for e in student.education
        ]) if student.education else "Not specified"
        
        projects_str = "\n".join([
            f"- {p.title}: {getattr(p, 'objective', '') or getattr(p, 'description', '')}" for p in student.projects[:4]
        ]) if student.projects else "None listed"
        
        research_str = "\n".join([
            f"- {r.title} at {r.organization}: {r.description}"
            for r in student.research_experience[:3]
        ]) if student.research_experience else "None listed"
        
        matches_str = "\n".join([
            f"- {m.get('student_item')} → {m.get('professor_item')}: {m.get('explanation', '')}"
            for m in match_analysis.get("matches", [])[:4]
        ]) if match_analysis.get("matches") else "General alignment with research focus"
        
        message = prompt.format_messages(
            professor_name=professor.name,
            department=professor.department,
            research_areas=", ".join(professor.research_areas[:5]) if professor.research_areas else "their research",
            student_name=student.student_name,
            education=education_str,
            skills=", ".join(student.get_all_skills()[:12]) if student.get_all_skills() else "various technical skills",
            projects=projects_str,
            research_experience=research_str,
            key_matches=matches_str
        )
        
        try:
            response = await self.llm.ainvoke(message)
            return self._get_content_str(response.content).strip()
            
        except Exception as e:
            self.logger.error(f"Cover letter generation failed: {e}")
            return f"[Cover letter generation failed. Please write manually.]"
