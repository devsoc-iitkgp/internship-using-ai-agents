"""Web search tool using Serper API (free tier: 2500 searches/month)."""

import asyncio
import aiohttp
from typing import List, Dict, Optional, Any
from tenacity import retry, stop_after_attempt, wait_fixed

from ..utils.config import settings
from ..utils.logger import AgentLogger


class WebSearchTool:
    """
    Web search tool for enriching professor profiles with research data.
    
    Uses Serper.dev Google Search API - free tier includes 2500 searches/month.
    """
    
    SERPER_API_URL = "https://google.serper.dev/search"
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or settings.serper_api_key
        self.logger = AgentLogger("WebSearchTool")
        
        if not self.api_key:
            self.logger.warning("Serper API key not configured - enrichment will be limited")
    
    @retry(stop=stop_after_attempt(3), wait=wait_fixed(2))
    async def search(
        self, 
        query: str, 
        max_results: int = 5,
        search_depth: str = "basic"
    ) -> List[Dict[str, Any]]:
        """
        Perform a web search using Serper API.
        
        Args:
            query: Search query string
            max_results: Maximum number of results to return
            search_depth: Ignored (kept for API compatibility)
            
        Returns:
            List of search results with title, url, and content
        """
        if not self.api_key:
            return []
        
        self.logger.info("Searching", query=query)
        
        try:
            headers = {
                "X-API-KEY": self.api_key,
                "Content-Type": "application/json"
            }
            
            payload = {
                "q": query,
                "num": max_results
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.SERPER_API_URL,
                    headers=headers,
                    json=payload
                ) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        self.logger.error(f"Serper API error: {response.status} - {error_text}")
                        return []
                    
                    data = await response.json()
            
            # Extract organic results
            organic_results = data.get("organic", [])
            self.logger.info(f"Found {len(organic_results)} results")
            
            return [
                {
                    "title": r.get("title", ""),
                    "url": r.get("link", ""),
                    "content": r.get("snippet", ""),
                    "score": r.get("position", 10) / 10,  # Convert position to score
                }
                for r in organic_results[:max_results]
            ]
            
        except Exception as e:
            self.logger.error(f"Search failed: {e}")
            return []
    
    async def search_professor(
        self, 
        name: str, 
        department: str,
        research_areas: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Search for additional information about a professor.
        
        Args:
            name: Professor's full name
            department: Department name
            research_areas: Known research areas for targeted search
            
        Returns:
            Dict with search results organized by category
        """
        results = {
            "general": [],
            "publications": [],
            "scholar": [],
        }
        
        # General search
        general_query = f"{name} IIT Kharagpur {department}"
        results["general"] = await self.search(general_query, max_results=3)
        
        # Publication search
        pub_query = f"{name} publications research papers"
        results["publications"] = await self.search(pub_query, max_results=3)
        
        # Google Scholar search
        scholar_query = f"{name} Google Scholar"
        results["scholar"] = await self.search(scholar_query, max_results=2)
        
        # Research area specific search if available
        if research_areas:
            area_query = f"{name} {' '.join(research_areas[:3])}"
            area_results = await self.search(area_query, max_results=2)
            results["general"].extend(area_results)
        
        return results
    
    def extract_scholar_links(self, results: Dict[str, Any]) -> List[str]:
        """Extract Google Scholar and academic profile links from search results."""
        scholar_links = []
        academic_domains = [
            "scholar.google.com",
            "dblp.org",
            "researchgate.net",
            "orcid.org",
            "semanticscholar.org"
        ]
        
        all_results = (
            results.get("general", []) +
            results.get("publications", []) +
            results.get("scholar", [])
        )
        
        for result in all_results:
            url = result.get("url", "")
            if any(domain in url for domain in academic_domains):
                if url not in scholar_links:
                    scholar_links.append(url)
        
        return scholar_links
