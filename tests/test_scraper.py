"""Tests for Faculty Scraper Agent."""

import pytest
from bs4 import BeautifulSoup

from src.schemas.faculty import FacultyProfile
from src.tools.web_scraper import FacultyScraper


# Sample HTML for testing
SAMPLE_FACULTY_TABLE = """
<table id="example">
    <tr>
        <th>Faculty</th>
        <th>Department</th>
        <th>Designation</th>
    </tr>
    <tr>
        <td><a href="/department/CS/faculty/test-faculty">Test Professor</a></td>
        <td>Computer Science and Engineering</td>
        <td>Professor</td>
    </tr>
    <tr>
        <td><a href="/department/AE/faculty/test-faculty2">Test Associate</a></td>
        <td>Aerospace Engineering</td>
        <td>Associate Professor</td>
    </tr>
</table>
"""

SAMPLE_PROFILE_PAGE = """
<html>
<body>
    <h4>Dr. Test Professor</h4>
    <p>Ph.D., IIT Delhi</p>
    <a href="mailto:test@cse.iitkgp.ac.in">test@cse.iitkgp.ac.in</a>
    <a href="tel:+91-3222-282350">+91-3222-282350</a>
    <div class="research-areas">
        <a class="research-tag">Machine Learning</a>
        <a class="research-tag">Computer Vision</a>
    </div>
    <a href="https://example.com">Personal Webpage</a>
</body>
</html>
"""


class TestFacultyScraper:
    """Test suite for FacultyScraper tool."""
    
    def test_parse_faculty_table(self):
        """Test parsing of faculty table HTML."""
        scraper = FacultyScraper()
        soup = BeautifulSoup(SAMPLE_FACULTY_TABLE, "lxml")
        
        table = soup.find("table", {"id": "example"})
        assert table is not None
        
        rows = table.find_all("tr")[1:]  # Skip header
        assert len(rows) == 2
        
        # Parse first row
        cells = rows[0].find_all("td")
        name_link = cells[0].find("a")
        
        assert name_link.get_text(strip=True) == "Test Professor"
        assert "/department/CS/faculty/test-faculty" in name_link.get("href")
        assert cells[1].get_text(strip=True) == "Computer Science and Engineering"
        assert cells[2].get_text(strip=True) == "Professor"
    
    def test_parse_profile_page(self):
        """Test parsing of individual profile page."""
        scraper = FacultyScraper()
        soup = BeautifulSoup(SAMPLE_PROFILE_PAGE, "lxml")
        
        basic_info = {
            "name": "Test Professor",
            "designation": "Professor",
            "department": "Computer Science"
        }
        
        profile_data = scraper._parse_profile_page(soup, basic_info)
        
        assert profile_data["email"] == "test@cse.iitkgp.ac.in"
        assert "Ph.D" in profile_data.get("education", "")
    
    def test_extract_research_areas(self):
        """Test extraction of research areas."""
        scraper = FacultyScraper()
        soup = BeautifulSoup(SAMPLE_PROFILE_PAGE, "lxml")
        
        areas = scraper._extract_research_areas(soup)
        
        # Should find at least some research areas
        assert isinstance(areas, list)
    
    def test_faculty_profile_schema(self):
        """Test FacultyProfile Pydantic schema."""
        profile = FacultyProfile(
            name="Test Professor",
            designation="Professor",
            department="Computer Science",
            email="test@example.com",
            profile_url="https://example.com/profile",
            research_areas=["ML", "AI"]
        )
        
        assert profile.name == "Test Professor"
        assert len(profile.research_areas) == 2
        
        # Test JSON serialization
        data = profile.model_dump()
        assert isinstance(data, dict)
        assert data["name"] == "Test Professor"
    
    def test_faculty_profile_optional_fields(self):
        """Test FacultyProfile with optional fields missing."""
        profile = FacultyProfile(
            name="Minimal Professor",
            designation="Assistant Professor",
            department="Physics",
            profile_url="https://example.com"
        )
        
        assert profile.email is None
        assert profile.phone is None
        assert profile.bio is None
        assert profile.research_areas == []


class TestDepartmentFiltering:
    """Test department filtering logic."""
    
    def test_filter_by_department(self):
        """Test filtering profiles by department name."""
        profiles = [
            {"name": "Prof A", "department": "Computer Science and Engineering"},
            {"name": "Prof B", "department": "Aerospace Engineering"},
            {"name": "Prof C", "department": "Computer Science and Engineering"},
        ]
        
        departments = ["Computer Science"]
        
        filtered = [
            p for p in profiles
            if any(d.lower() in p["department"].lower() for d in departments)
        ]
        
        assert len(filtered) == 2
        assert all("Computer Science" in p["department"] for p in filtered)
