"""
Agent 1: Faculty Scraping Agent

Responsible for scraping faculty data from IIT Kharagpur website.
"""

import json
from pathlib import Path
from typing import List, Optional, Dict, Any

from ..tools.web_scraper import FacultyScraper
from ..schemas.faculty import FacultyProfile
from ..utils.config import settings
from ..utils.logger import AgentLogger


class FacultyScraperAgent:
    """
    Faculty Scraping Agent - Agent 1 in the pipeline.
    
    Collects professor data from IIT Kharagpur faculty directory.
    
    Responsibilities:
    - Scrape all faculty listings department-wise
    - Visit individual faculty profile pages
    - Extract structured data (name, designation, email, etc.)
    - Store output in structured JSON
    """
    
    def __init__(self):
        self.logger = AgentLogger("FacultyScraperAgent")
        self.scraper = FacultyScraper()
    
    async def run(
        self,
        departments: Optional[List[str]] = None,
        limit: Optional[int] = None,
        save_to_file: bool = True
    ) -> List[FacultyProfile]:
        """
        Execute the faculty scraping pipeline.
        
        Args:
            departments: Optional list of department names to filter
            limit: Optional limit on number of profiles to scrape
            save_to_file: Whether to save results to JSON file
            
        Returns:
            List of scraped FacultyProfile objects
        """
        self.logger.info("Starting faculty scraping agent")
        
        profiles: List[FacultyProfile] = []
        
        async with self.scraper:
            profiles = await self.scraper.scrape_all_faculty(
                departments=departments,
                limit=limit
            )
        
        self.logger.info(f"Scraped {len(profiles)} faculty profiles")
        
        if save_to_file and profiles:
            output_path = self._save_profiles(profiles)
            self.logger.info(f"Saved profiles to {output_path}")
        
        return profiles
    
    async def run_single(self, profile_url: str) -> FacultyProfile:
        """
        Scrape a single faculty profile.
        
        Args:
            profile_url: URL of the faculty profile page
            
        Returns:
            FacultyProfile object
        """
        self.logger.info("Scraping single profile", url=profile_url)
        
        async with self.scraper:
            profile = await self.scraper.scrape_faculty_profile(profile_url)
        
        return profile
    
    def _save_profiles(self, profiles: List[FacultyProfile]) -> Path:
        """Save profiles to JSON file."""
        settings.ensure_directories()
        
        output_path = settings.data_dir / "raw" / "faculty_profiles.json"
        
        data = [p.model_dump() for p in profiles]
        
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        return output_path
    
    @staticmethod
    def load_profiles(file_path: Optional[Path] = None) -> List[FacultyProfile]:
        """
        Load previously scraped profiles from JSON file.
        
        Args:
            file_path: Path to JSON file, defaults to standard location
            
        Returns:
            List of FacultyProfile objects
        """
        if file_path is None:
            file_path = settings.data_dir / "raw" / "faculty_profiles.json"
        
        if not file_path.exists():
            return []
        
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        return [FacultyProfile(**item) for item in data]
    
    def get_output_schema(self) -> Dict[str, Any]:
        """Return the JSON schema for agent output."""
        return FacultyProfile.model_json_schema()
