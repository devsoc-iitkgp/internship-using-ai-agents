"""
Agent 2: Research Enrichment Agent

Responsible for enriching faculty profiles with additional research data.
"""

import json
from pathlib import Path
from typing import List, Optional, Dict, Any

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

from ..tools.search_tool import WebSearchTool
from ..schemas.faculty import FacultyProfile
from ..schemas.research import EnrichedProfile, Publication
from ..utils.config import settings
from ..utils.logger import AgentLogger


KEYWORD_EXTRACTION_PROMPT = """You are an expert at analyzing academic profiles.

Given the following professor information, extract key expertise keywords that would be useful for matching with potential research interns.

Professor Name: {name}
Department: {department}
Research Areas: {research_areas}
Bio: {bio}

Publications/Projects found from web search:
{search_context}

Extract 5-10 specific, technical keywords that represent this professor's expertise.
Focus on:
- Specific technologies and tools
- Research methodologies
- Application domains
- Technical skills required

Output ONLY a JSON array of strings, nothing else. Example: ["machine learning", "computer vision", "PyTorch"]
"""


class ResearchEnrichmentAgent:
    """
    Research Enrichment Agent - Agent 2 in the pipeline.
    
    Enriches faculty profiles with additional research data from web searches.
    
    Responsibilities:
    - Perform targeted web searches for each professor
    - Extract research areas, publications, and projects
    - Generate expertise keywords using LLM
    - Calculate enrichment confidence scores
    """
    
    def __init__(self, api_key: Optional[str] = None):
        self.logger = AgentLogger("ResearchEnrichmentAgent")
        self.search_tool = WebSearchTool()
        self.llm = ChatOpenAI(
            model=settings.llm_model,
            temperature=0.2,
            api_key=api_key or settings.openai_api_key
        )
    
    async def run(
        self,
        profiles: List[FacultyProfile],
        save_to_file: bool = True
    ) -> List[EnrichedProfile]:
        """
        Enrich a list of faculty profiles with research data.
        
        Args:
            profiles: List of FacultyProfile objects from Agent 1
            save_to_file: Whether to save results to JSON file
            
        Returns:
            List of EnrichedProfile objects
        """
        self.logger.info(f"Enriching {len(profiles)} faculty profiles")
        
        enriched_profiles: List[EnrichedProfile] = []
        
        for i, profile in enumerate(profiles):
            try:
                enriched = await self.enrich_profile(profile)
                enriched_profiles.append(enriched)
                self.logger.info(
                    f"Enriched {i+1}/{len(profiles)}",
                    name=profile.name,
                    confidence=enriched.enrichment_confidence
                )
            except Exception as e:
                self.logger.error(f"Failed to enrich {profile.name}: {e}")
                # Create basic enriched profile without additional data
                enriched_profiles.append(
                    EnrichedProfile.from_faculty_profile(profile)
                )
        
        if save_to_file and enriched_profiles:
            output_path = self._save_profiles(enriched_profiles)
            self.logger.info(f"Saved enriched profiles to {output_path}")
        
        return enriched_profiles
    
    async def enrich_profile(self, profile: FacultyProfile) -> EnrichedProfile:
        """
        Enrich a single faculty profile.
        
        Args:
            profile: FacultyProfile to enrich
            
        Returns:
            EnrichedProfile with additional research data
        """
        # Start with base profile data
        enriched = EnrichedProfile.from_faculty_profile(profile)
        
        # Perform web search
        search_results = await self.search_tool.search_professor(
            name=profile.name,
            department=profile.department,
            research_areas=profile.research_areas
        )
        
        # Extract scholar links
        enriched.scholar_links = self.search_tool.extract_scholar_links(search_results)
        
        # Extract expertise keywords using LLM
        search_context = self._format_search_context(search_results)
        keywords = await self._extract_keywords(profile, search_context)
        enriched.expertise_keywords = keywords
        
        # Parse publications from search results (basic extraction)
        publications = self._extract_publications(search_results)
        enriched.recent_publications = publications
        
        # Calculate confidence score
        enriched.enrichment_confidence = self._calculate_confidence(enriched)
        
        return enriched
    
    def _format_search_context(self, search_results: Dict[str, Any]) -> str:
        """Format search results into context string for LLM."""
        context_parts = []
        
        for category, results in search_results.items():
            if results:
                for result in results[:2]:  # Top 2 per category
                    context_parts.append(
                        f"[{category}] {result.get('title', '')}: {result.get('content', '')[:300]}"
                    )
        
        return "\n\n".join(context_parts) if context_parts else "No additional information found."
    
    async def _extract_keywords(
        self, 
        profile: FacultyProfile, 
        search_context: str
    ) -> List[str]:
        """Extract expertise keywords using LLM."""
        try:
            prompt = ChatPromptTemplate.from_template(KEYWORD_EXTRACTION_PROMPT)
            
            message = prompt.format_messages(
                name=profile.name,
                department=profile.department,
                research_areas=", ".join(profile.research_areas) if profile.research_areas else "Not specified",
                bio=profile.bio or "Not available",
                search_context=search_context
            )
            
            response = await self.llm.ainvoke(message)
            
            # Parse JSON array from response
            content = response.content.strip()
            if content.startswith("["):
                keywords = json.loads(content)
                return keywords if isinstance(keywords, list) else []
            
            return []
            
        except Exception as e:
            self.logger.error(f"Keyword extraction failed: {e}")
            return profile.research_areas.copy() if profile.research_areas else []
    
    def _extract_publications(
        self, 
        search_results: Dict[str, Any]
    ) -> List[Publication]:
        """Extract publication information from search results."""
        publications = []
        
        pub_results = search_results.get("publications", [])
        for result in pub_results[:5]:
            title = result.get("title", "")
            if title and len(title) > 10:
                publications.append(Publication(
                    title=title,
                    authors=[],  # Would need more parsing
                    venue=None,
                    year=None,
                    url=result.get("url")
                ))
        
        return publications
    
    def _calculate_confidence(self, profile: EnrichedProfile) -> float:
        """Calculate enrichment confidence score based on available data."""
        score = 0.0
        
        # Base score for having profile data
        if profile.bio:
            score += 0.2
        if profile.research_areas:
            score += 0.2
        
        # Bonus for enriched data
        if profile.expertise_keywords:
            score += 0.2
        if profile.scholar_links:
            score += 0.2
        if profile.recent_publications:
            score += 0.2
        
        return min(score, 1.0)
    
    def _save_profiles(self, profiles: List[EnrichedProfile]) -> Path:
        """Save enriched profiles to JSON file."""
        settings.ensure_directories()
        
        output_path = settings.data_dir / "enriched" / "enriched_profiles.json"
        
        data = [p.model_dump() for p in profiles]
        
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        return output_path
    
    @staticmethod
    def load_profiles(file_path: Optional[Path] = None) -> List[EnrichedProfile]:
        """Load previously enriched profiles from JSON file."""
        if file_path is None:
            file_path = settings.data_dir / "enriched" / "enriched_profiles.json"
        
        if not file_path.exists():
            return []
        
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        return [EnrichedProfile(**item) for item in data]
