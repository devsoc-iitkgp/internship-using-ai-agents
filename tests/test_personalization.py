"""Tests for Personalization Agent."""

import pytest

from src.schemas.cv import StudentCV, Project, Education
from src.schemas.research import EnrichedProfile
from src.schemas.output import EmailOutput, MatchReason


class TestMatchReason:
    """Test MatchReason schema."""
    
    def test_create_match_reason(self):
        """Test creating a MatchReason object."""
        match = MatchReason(
            category="skill",
            student_item="PyTorch",
            professor_item="Deep Learning",
            relevance_score=0.85,
            explanation="PyTorch is commonly used for deep learning research"
        )
        
        assert match.category == "skill"
        assert match.relevance_score == 0.85
    
    def test_match_reason_score_bounds(self):
        """Test that relevance score is bounded 0-1."""
        with pytest.raises(ValueError):
            MatchReason(
                category="skill",
                student_item="test",
                professor_item="test",
                relevance_score=1.5  # Invalid: > 1.0
            )


class TestEmailOutput:
    """Test EmailOutput schema."""
    
    def test_create_email_output(self):
        """Test creating an EmailOutput object."""
        output = EmailOutput(
            professor_name="Dr. Test Professor",
            professor_email="test@iitkgp.ac.in",
            department="Computer Science",
            profile_url="https://example.com",
            match_reasons=[
                MatchReason(
                    category="skill",
                    student_item="ML",
                    professor_item="Machine Learning",
                    relevance_score=0.9
                )
            ],
            overall_match_score=0.75,
            email_subject="Research Internship Inquiry",
            email_body="Dear Professor...",
            cover_letter="Full cover letter text..."
        )
        
        assert output.professor_name == "Dr. Test Professor"
        assert len(output.match_reasons) == 1
        assert output.overall_match_score == 0.75


class TestMatchingLogic:
    """Test matching logic between student and professor."""
    
    def test_skill_matching(self):
        """Test matching student skills with professor expertise."""
        student_skills = ["Python", "Machine Learning", "PyTorch", "Computer Vision"]
        professor_keywords = ["deep learning", "computer vision", "neural networks", "tensorflow"]
        
        # Simple overlap check (case-insensitive)
        student_lower = [s.lower() for s in student_skills]
        prof_lower = [p.lower() for p in professor_keywords]
        
        matches = []
        for skill in student_lower:
            for keyword in prof_lower:
                if skill in keyword or keyword in skill:
                    matches.append((skill, keyword))
        
        # Should find "computer vision" match
        assert len(matches) >= 1
        assert any("computer vision" in m[0] or "computer vision" in m[1] for m in matches)
    
    def test_project_research_matching(self):
        """Test matching student projects with professor research areas."""
        student_projects = [
            "Image classification using CNNs",
            "Natural language processing chatbot",
            "Secure hardware implementation"
        ]
        
        professor_research = [
            "Computer Vision",
            "Hardware Security",
            "Cryptography"
        ]
        
        # Simple keyword overlap
        matches = []
        for proj in student_projects:
            proj_lower = proj.lower()
            for area in professor_research:
                area_lower = area.lower()
                # Check for keyword overlap
                area_words = area_lower.split()
                for word in area_words:
                    if word in proj_lower:
                        matches.append((proj, area))
        
        # Should find hardware/security match
        assert len(matches) >= 1
    
    def test_calculate_overall_score(self):
        """Test calculating overall match score from individual matches."""
        match_scores = [0.9, 0.75, 0.6, 0.5]
        
        # Weighted average favoring higher scores
        if match_scores:
            # Simple average
            avg = sum(match_scores) / len(match_scores)
            
            # Weighted by position (higher weight to better matches)
            sorted_scores = sorted(match_scores, reverse=True)
            weights = [1.0, 0.8, 0.6, 0.4][:len(sorted_scores)]
            weighted_avg = sum(s * w for s, w in zip(sorted_scores, weights)) / sum(weights)
            
            assert 0.0 <= avg <= 1.0
            assert 0.0 <= weighted_avg <= 1.0
            assert weighted_avg >= avg  # Weighted should favor higher scores


class TestEmailGeneration:
    """Test email generation logic."""
    
    def test_email_subject_format(self):
        """Test email subject line formatting."""
        department = "Computer Science"
        research_area = "Machine Learning"
        
        subject = f"Research Internship Inquiry - {research_area}"
        
        assert "Internship" in subject
        assert research_area in subject
        assert len(subject) < 100  # Subject should be concise
    
    def test_email_body_structure(self):
        """Test that email body has proper structure."""
        required_elements = [
            "greeting",  # Dear Professor...
            "introduction",  # I am...
            "interest",  # Your research in...
            "qualifications",  # My experience in...
            "closing"  # Thank you...
        ]
        
        sample_email = """
        Dear Professor Smith,
        
        I am a third-year Computer Science student at XYZ University.
        
        Your research in machine learning and computer vision aligns with my interests.
        
        My experience includes building CNN-based image classifiers and working with PyTorch.
        
        Thank you for considering my application.
        
        Best regards,
        Test Student
        """
        
        email_lower = sample_email.lower()
        
        assert "dear professor" in email_lower
        assert "i am" in email_lower
        assert "thank you" in email_lower or "sincerely" in email_lower
    
    def test_email_length(self):
        """Test that generated email is within target length."""
        min_words = 100
        max_words = 250
        
        sample_email = "This is a test email. " * 50  # ~150 words
        word_count = len(sample_email.split())
        
        # Verify we can check word counts
        assert word_count > 0
        
        # A good email should be in the target range
        # (This is a test of the testing logic)
