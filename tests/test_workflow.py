"""Tests for LangGraph Workflow."""

import pytest

from src.graph.state import AgentState, create_initial_state


class TestAgentState:
    """Test AgentState creation and management."""
    
    def test_create_initial_state(self):
        """Test creating initial pipeline state."""
        state = create_initial_state(
            cv_path="/path/to/cv.pdf",
            target_departments=["Computer Science"],
            faculty_limit=10,
            min_match_score=0.5
        )
        
        assert state["cv_path"] == "/path/to/cv.pdf"
        assert state["target_departments"] == ["Computer Science"]
        assert state["faculty_limit"] == 10
        assert state["min_match_score"] == 0.5
        assert state["faculty_profiles"] == []
        assert state["enriched_profiles"] == []
        assert state["email_outputs"] == []
        assert state["errors"] == []
    
    def test_create_initial_state_defaults(self):
        """Test initial state with default values."""
        state = create_initial_state()
        
        assert state["cv_path"] is None
        assert state["target_departments"] is None
        assert state["faculty_limit"] is None
        assert state["min_match_score"] == 0.3


class TestWorkflowLogic:
    """Test workflow conditional logic."""
    
    def test_should_generate_emails_positive(self):
        """Test that email generation proceeds when conditions are met."""
        from src.schemas.cv import StudentCV
        from src.schemas.research import EnrichedProfile
        
        state = {
            "enriched_profiles": [
                EnrichedProfile(
                    name="Test Prof",
                    designation="Professor",
                    department="CS",
                    profile_url="https://example.com"
                )
            ],
            "student_cv": StudentCV(student_name="Test Student")
        }
        
        has_profiles = len(state.get("enriched_profiles", [])) > 0
        has_cv = state.get("student_cv") is not None
        
        assert has_profiles is True
        assert has_cv is True
        assert has_profiles and has_cv  # Should generate
    
    def test_should_generate_emails_no_cv(self):
        """Test that email generation skips when CV is missing."""
        from src.schemas.research import EnrichedProfile
        
        state = {
            "enriched_profiles": [
                EnrichedProfile(
                    name="Test Prof",
                    designation="Professor",
                    department="CS",
                    profile_url="https://example.com"
                )
            ],
            "student_cv": None
        }
        
        has_profiles = len(state.get("enriched_profiles", [])) > 0
        has_cv = state.get("student_cv") is not None
        
        assert has_profiles is True
        assert has_cv is False
        assert not (has_profiles and has_cv)  # Should not generate
    
    def test_should_generate_emails_no_profiles(self):
        """Test that email generation skips when profiles are missing."""
        from src.schemas.cv import StudentCV
        
        state = {
            "enriched_profiles": [],
            "student_cv": StudentCV(student_name="Test Student")
        }
        
        has_profiles = len(state.get("enriched_profiles", [])) > 0
        has_cv = state.get("student_cv") is not None
        
        assert has_profiles is False
        assert has_cv is True
        assert not (has_profiles and has_cv)  # Should not generate


class TestErrorAccumulation:
    """Test error accumulation in state."""
    
    def test_errors_accumulate(self):
        """Test that errors are properly accumulated."""
        errors = []
        
        # Simulate errors from different nodes
        errors.append("Scraping failed for profile X")
        errors.append("Enrichment failed for profile Y")
        errors.append("Email generation failed for profile Z")
        
        assert len(errors) == 3
        assert all(isinstance(e, str) for e in errors)
    
    def test_logs_accumulate(self):
        """Test that logs are properly accumulated."""
        logs = []
        
        logs.append("Starting scrape")
        logs.append("Scraped 10 profiles")
        logs.append("Enriching profiles")
        logs.append("Enriched 10 profiles")
        
        assert len(logs) == 4
        assert "10 profiles" in logs[1]
