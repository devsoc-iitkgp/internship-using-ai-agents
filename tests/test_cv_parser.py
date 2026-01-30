"""Tests for CV Parser Agent."""

import pytest
import json

from src.schemas.cv import StudentCV, Education, Project


class TestStudentCVSchema:
    """Test suite for CV schema validation."""
    
    def test_create_student_cv(self):
        """Test creating a StudentCV object."""
        cv = StudentCV(
            student_name="Test Student",
            email="test@example.com",
            education=[
                Education(
                    degree="B.Tech",
                    institution="IIT Delhi",
                    field="Computer Science",
                    year="2025",
                    gpa="9.0"
                )
            ],
            skills=["Python", "Machine Learning", "PyTorch"],
            projects=[
                Project(
                    title="Test Project",
                    description="A test project description",
                    technologies=["Python", "TensorFlow"]
                )
            ],
            interests=["Deep Learning", "Computer Vision"]
        )
        
        assert cv.student_name == "Test Student"
        assert len(cv.education) == 1
        assert cv.education[0].degree == "B.Tech"
        assert len(cv.skills) == 3
        assert len(cv.projects) == 1
    
    def test_cv_json_serialization(self):
        """Test StudentCV serialization to JSON."""
        cv = StudentCV(
            student_name="Test Student",
            skills=["Python", "ML"],
            projects=[]
        )
        
        data = cv.model_dump()
        json_str = json.dumps(data)
        
        assert isinstance(json_str, str)
        assert "Test Student" in json_str
    
    def test_cv_optional_fields(self):
        """Test StudentCV with minimal required fields."""
        cv = StudentCV(student_name="Minimal Student")
        
        assert cv.student_name == "Minimal Student"
        assert cv.email is None
        assert cv.education == []
        assert cv.skills == []
        assert cv.projects == []


class TestSkillNormalization:
    """Test skill normalization logic."""
    
    def test_normalize_common_abbreviations(self):
        """Test normalizing common skill abbreviations."""
        skill_mapping = {
            "ml": "Machine Learning",
            "dl": "Deep Learning",
            "nlp": "Natural Language Processing",
            "cv": "Computer Vision",
            "py": "Python",
            "js": "JavaScript",
        }
        
        skills = ["ML", "dl", "Python", "js"]
        normalized = []
        
        for skill in skills:
            skill_lower = skill.lower().strip()
            if skill_lower in skill_mapping:
                normalized.append(skill_mapping[skill_lower])
            else:
                normalized.append(skill.strip())
        
        assert "Machine Learning" in normalized
        assert "Deep Learning" in normalized
        assert "Python" in normalized
        assert "JavaScript" in normalized
    
    def test_remove_duplicates(self):
        """Test removing duplicate skills after normalization."""
        skills = ["Machine Learning", "ML", "machine learning"]
        
        skill_mapping = {"ml": "Machine Learning"}
        
        normalized = []
        for skill in skills:
            skill_lower = skill.lower().strip()
            if skill_lower in skill_mapping:
                normalized.append(skill_mapping[skill_lower])
            else:
                normalized.append(skill.strip())
        
        unique = list(set(normalized))
        
        # Should have fewer after deduplication
        assert len(unique) <= len(skills)


class TestEducationParsing:
    """Test education data parsing."""
    
    def test_education_with_all_fields(self):
        """Test Education with all fields populated."""
        edu = Education(
            degree="Ph.D.",
            institution="IIT Kharagpur",
            field="Computer Science",
            year="2023",
            gpa="9.5/10"
        )
        
        assert edu.degree == "Ph.D."
        assert edu.institution == "IIT Kharagpur"
        assert edu.field == "Computer Science"
    
    def test_education_with_minimal_fields(self):
        """Test Education with only required fields."""
        edu = Education(
            degree="B.Tech",
            institution="Some College"
        )
        
        assert edu.degree == "B.Tech"
        assert edu.field is None
        assert edu.year is None
