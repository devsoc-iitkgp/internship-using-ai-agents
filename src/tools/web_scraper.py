"""Web scraper tool using Playwright for JavaScript-rendered pages."""

import asyncio
from typing import List, Dict, Optional, Any
from playwright.async_api import async_playwright, Page, Browser
from bs4 import BeautifulSoup
from tenacity import retry, stop_after_attempt, wait_exponential

from ..utils.config import settings
from ..utils.logger import AgentLogger
from ..schemas.faculty import FacultyProfile


# Department codes for IIT KGP
DEPARTMENT_CODES = {
    "Computer Science": "CS",
    "CSE": "CS",
    "CS": "CS",
    "Electronics": "EC",
    "ECE": "EC",
    "EC": "EC",
    "E&ECE": "EC",
    "Electrical": "EE",
    "EE": "EE",
    "Mechanical": "ME",
    "ME": "ME",
    "Chemical": "CH",
    "CH": "CH",
    "Civil": "CE",
    "CE": "CE",
    "Mathematics": "MA",
    "Maths": "MA",
    "Math": "MA",
    "MA": "MA",
    "Physics": "PH",
    "PH": "PH",
    "Chemistry": "CY",
    "CY": "CY",
    "Metallurgical": "MT",
    "Materials": "MT",
    "MT": "MT",
    "Aerospace": "AE",
    "AE": "AE",
    "Industrial": "IM",
    "IM": "IM",
    "Architecture": "AR",
    "AR": "AR",
}


class FacultyScraper:
    """
    Playwright-based web scraper for IIT KGP faculty pages.
    
    Uses department-specific URLs for accurate faculty data.
    """
    
    def __init__(self):
        self.logger = AgentLogger("FacultyScraper")
        self.browser: Optional[Browser] = None
        self.delay = settings.scraper_delay
        self.base_url = settings.faculty_base_url
        
    async def __aenter__(self):
        """Initialize browser on context entry."""
        playwright = await async_playwright().start()
        self.browser = await playwright.chromium.launch(headless=True)
        self.logger.info("Browser initialized")
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Close browser on context exit."""
        if self.browser:
            await self.browser.close()
            self.logger.info("Browser closed")
    
    def _get_department_code(self, department: str) -> Optional[str]:
        """Convert department name to IIT KGP department code."""
        return DEPARTMENT_CODES.get(department)
    
    async def scrape_department_faculty(
        self, 
        department_code: str
    ) -> List[Dict[str, Any]]:
        """
        Scrape faculty from a specific department page.
        
        Args:
            department_code: IIT KGP department code (e.g., 'CS', 'EC', 'EE')
            
        Returns:
            List of faculty info dicts
        """
        if not self.browser:
            raise RuntimeError("Browser not initialized. Use 'async with' context.")
        
        page = await self.browser.new_page()
        faculty_list = []
        
        try:
            # Navigate to department page
            dept_url = f"{self.base_url}/department/{department_code}"
            self.logger.info(f"Loading department page", url=dept_url)
            await page.goto(dept_url, wait_until="networkidle")
            await asyncio.sleep(1)
            
            # Select faculty from dropdown
            try:
                await page.select_option("#show_people_former_staff", "faculty")
                await asyncio.sleep(1.5)  # Wait for faculty to load
            except Exception:
                self.logger.warning(f"Could not find faculty dropdown for {department_code}")
            
            # Get page content
            content = await page.content()
            soup = BeautifulSoup(content, "lxml")
            
            # Find all faculty cards - they are <a> tags linking to /faculty/ pages
            faculty_cards = soup.find_all("a", href=lambda h: h and "/faculty/" in h)
            
            self.logger.info(f"Found {len(faculty_cards)} faculty cards")
            
            for card in faculty_cards:
                try:
                    # Extract name from .hndg span
                    name_elem = card.find("span", class_="hndg")
                    if not name_elem:
                        # Fallback to first span with substantial text
                        for span in card.find_all("span"):
                            text = span.get_text(strip=True)
                            if text and len(text) > 3 and "@" not in text:
                                name_elem = span
                                break
                    
                    if not name_elem:
                        continue
                    
                    name = name_elem.get_text(strip=True)
                    if not name or len(name) < 2:
                        continue
                    
                    # Get profile URL
                    href = card.get("href", "")
                    if href.startswith("http"):
                        profile_url = href
                    else:
                        profile_url = f"{self.base_url}{href}" if href.startswith("/") else f"{self.base_url}/{href}"
                    
                    # Extract email - look for @ in text
                    email = None
                    card_text = card.get_text()
                    import re
                    email_match = re.search(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', card_text)
                    if email_match:
                        email = email_match.group()
                    
                    # Extract designation from .tx22 i
                    designation = ""
                    tx22_elem = card.find("span", class_="tx22")
                    if tx22_elem:
                        i_elem = tx22_elem.find("i")
                        if i_elem:
                            designation = i_elem.get_text(strip=True)
                    
                    # Extract research areas - text after "Research Area(s) :"
                    research_areas = []
                    if "Research Area" in card_text:
                        research_match = re.search(r'Research Area\(s\)\s*:\s*(.+)', card_text, re.DOTALL)
                        if research_match:
                            research_text = research_match.group(1).strip()
                            # Clean up the text
                            research_text = research_text.split('\n')[0]  # Take first line
                            research_areas = [a.strip() for a in research_text.split(";") if a.strip()]
                    
                    # Extract phone - look for extension number
                    phone = None
                    phone_match = re.search(r'\b\d{5}\b', card_text)
                    if phone_match:
                        phone = phone_match.group()
                    
                    faculty_info = {
                        "name": name,
                        "email": email,
                        "profile_url": profile_url,
                        "department": department_code,
                        "designation": designation,
                        "research_areas": research_areas,
                        "phone": phone,
                    }
                    
                    if faculty_info["name"] and faculty_info["profile_url"]:
                        faculty_list.append(faculty_info)
                        
                except Exception as e:
                    self.logger.warning(f"Error parsing faculty card: {e}")
                    continue
            
            self.logger.info(f"Scraped {len(faculty_list)} faculty from department {department_code}")
            
        except Exception as e:
            self.logger.error(f"Error scraping department {department_code}: {e}")
            raise
        finally:
            await page.close()
        
        return faculty_list
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    async def scrape_faculty_profile(
        self, 
        profile_url: str,
        basic_info: Optional[Dict[str, str]] = None
    ) -> FacultyProfile:
        """
        Scrape detailed information from a faculty profile page.
        
        Args:
            profile_url: URL of the faculty profile page
            basic_info: Optional dict with pre-scraped basic info
            
        Returns:
            FacultyProfile with all available information
        """
        if not self.browser:
            raise RuntimeError("Browser not initialized. Use 'async with' context.")
        
        page = await self.browser.new_page()
        
        try:
            self.logger.info("Scraping profile", url=profile_url)
            await page.goto(profile_url, wait_until="networkidle")
            await asyncio.sleep(self.delay)
            
            content = await page.content()
            soup = BeautifulSoup(content, "lxml")
            
            # Start with basic info
            profile_data = {
                "name": basic_info.get("name", "") if basic_info else "",
                "designation": basic_info.get("designation", "") if basic_info else "",
                "department": basic_info.get("department", "") if basic_info else "",
                "email": basic_info.get("email") if basic_info else None,
                "phone": basic_info.get("phone") if basic_info else None,
                "research_areas": basic_info.get("research_areas", []) if basic_info else [],
                "profile_url": profile_url,
            }
            
            # Try to get more detailed info from profile page
            # Find name from page if not in basic_info
            if not profile_data["name"]:
                name_elem = soup.find("h4") or soup.find("h3")
                if name_elem:
                    profile_data["name"] = name_elem.get_text(strip=True)
            
            # Extract email from profile page if not in basic_info
            if not profile_data["email"]:
                email_link = soup.find("a", href=lambda h: h and "mailto:" in h)
                if email_link:
                    profile_data["email"] = email_link.get("href").replace("mailto:", "")
            
            # Extract bio
            bio = await self._extract_bio(page, soup)
            if bio:
                profile_data["bio"] = bio
            
            # Extract research areas if not already present
            if not profile_data["research_areas"]:
                profile_data["research_areas"] = self._extract_research_areas(soup)
            
            # Extract personal webpage
            webpage_link = soup.find("a", string=lambda s: s and "Personal Webpage" in str(s))
            if webpage_link:
                profile_data["personal_webpage"] = webpage_link.get("href")
            
            return FacultyProfile(**profile_data)
            
        except Exception as e:
            self.logger.error(f"Error scraping profile: {e}", url=profile_url)
            raise
        finally:
            await page.close()
    
    async def _extract_bio(self, page: Page, soup: BeautifulSoup) -> Optional[str]:
        """Extract bio/research statement from profile page."""
        
        # Try to find bio in visible content first
        bio_section = soup.find(id="biosketch") or soup.find(class_="bio-sketch")
        if bio_section:
            return bio_section.get_text(strip=True)[:2000]
        
        # Try clicking on Bio Sketch tab
        try:
            bio_tab = page.locator("text=Bio Sketch")
            if await bio_tab.count() > 0:
                await bio_tab.first.click()
                await asyncio.sleep(0.5)
                
                content = await page.content()
                soup = BeautifulSoup(content, "lxml")
                
                tab_content = soup.find(class_="tab-pane active") or soup.find(class_="tab-content")
                if tab_content:
                    return tab_content.get_text(strip=True)[:2000]
        except Exception:
            pass
        
        return None
    
    def _extract_research_areas(self, soup: BeautifulSoup) -> List[str]:
        """Extract research areas/interests from profile."""
        research_areas = []
        
        research_section = soup.find_all("a", class_=lambda c: c and "research" in str(c).lower())
        for link in research_section:
            area = link.get_text(strip=True)
            if area and area not in research_areas:
                research_areas.append(area)
        
        return research_areas[:10]
    
    async def scrape_faculty_list(
        self, 
        departments: Optional[List[str]] = None
    ) -> List[Dict[str, str]]:
        """
        Scrape faculty from department-specific pages.
        
        Args:
            departments: List of department names/codes to scrape
            
        Returns:
            List of dicts with faculty info
        """
        if not self.browser:
            raise RuntimeError("Browser not initialized. Use 'async with' context.")
        
        all_faculty = []
        
        # Default to CS if no departments specified
        if not departments:
            departments = ["CS"]
        
        # Convert department names to codes
        dept_codes = set()
        for dept in departments:
            code = self._get_department_code(dept)
            if code:
                dept_codes.add(code)
            elif dept.upper() in DEPARTMENT_CODES.values():
                dept_codes.add(dept.upper())
        
        # If no valid codes, default to CS
        if not dept_codes:
            dept_codes = {"CS"}
        
        self.logger.info(f"Scraping departments: {dept_codes}")
        
        # Scrape each department
        for code in dept_codes:
            try:
                faculty = await self.scrape_department_faculty(code)
                all_faculty.extend(faculty)
            except Exception as e:
                self.logger.error(f"Failed to scrape department {code}: {e}")
        
        self.logger.info(f"Total faculty scraped: {len(all_faculty)}")
        return all_faculty
    
    async def scrape_all_faculty(
        self,
        departments: Optional[List[str]] = None,
        limit: Optional[int] = None
    ) -> List[FacultyProfile]:
        """
        Scrape all faculty profiles from specified departments.
        
        Args:
            departments: List of department names to filter
            limit: Optional limit on number of profiles to scrape
            
        Returns:
            List of FacultyProfile objects
        """
        faculty_list = await self.scrape_faculty_list(departments)
        
        if limit:
            faculty_list = faculty_list[:limit]
        
        self.logger.info(f"Scraping {len(faculty_list)} faculty profiles")
        
        profiles = []
        for i, faculty in enumerate(faculty_list):
            if faculty.get("profile_url"):
                try:
                    profile = await self.scrape_faculty_profile(
                        faculty["profile_url"],
                        faculty
                    )
                    profiles.append(profile)
                    self.logger.info(
                        f"Scraped {i+1}/{len(faculty_list)}",
                        name=profile.name
                    )
                except Exception as e:
                    self.logger.error(f"Failed to scrape {faculty.get('name')}: {e}")
        
        return profiles
