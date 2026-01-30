"""Department recommendation based on CV skills and interests."""

from typing import List, Set
from ..schemas.cv import StudentCV


# Mapping of skills/interests to relevant IIT KGP departments
SKILL_TO_DEPARTMENT_MAP = {
    # Computer Science & Engineering
    "Machine Learning": ["Computer Science", "Electronics", "Electrical"],
    "Deep Learning": ["Computer Science", "Electronics", "Electrical"],
    "Artificial Intelligence": ["Computer Science", "Electronics"],
    "Natural Language Processing": ["Computer Science"],
    "Computer Vision": ["Computer Science", "Electronics"],
    "Data Science": ["Computer Science", "Mathematics"],
    "Algorithm": ["Computer Science", "Mathematics"],
    "Data Structure": ["Computer Science"],
    "Web Development": ["Computer Science"],
    "Python": ["Computer Science", "Electronics", "Electrical"],
    "C++": ["Computer Science", "Electronics"],
    "JavaScript": ["Computer Science"],
    "React": ["Computer Science"],
    "Next.js": ["Computer Science"],
    "Software Engineering": ["Computer Science"],
    "MLOps": ["Computer Science"],
    "DevOps": ["Computer Science"],
    "Cloud Computing": ["Computer Science"],
    "AWS": ["Computer Science"],
    "Docker": ["Computer Science"],
    "Kubernetes": ["Computer Science"],
    
    # Electronics & Electrical
    "Electronics": ["Electronics", "Electrical"],
    "VLSI": ["Electronics", "Electrical"],
    "Embedded Systems": ["Electronics", "Electrical", "Computer Science"],
    "Signal Processing": ["Electronics", "Electrical"],
    "Control Systems": ["Electrical", "Electronics"],
    "Power Systems": ["Electrical"],
    "FPGA": ["Electronics", "Electrical", "Computer Science"],
    "IoT": ["Electronics", "Electrical", "Computer Science"],
    
    # Blockchain & Cryptography
    "Blockchain": ["Computer Science", "Electronics"],
    "Cryptography": ["Computer Science", "Mathematics"],
    "Solidity": ["Computer Science"],
    "Smart Contracts": ["Computer Science"],
    
    # Finance & Quantitative
    "Quantitative Finance": ["Mathematics", "Computer Science", "Industrial"],
    "Financial Engineering": ["Mathematics", "Industrial"],
    "Trading": ["Mathematics", "Computer Science"],
    "Time Series": ["Mathematics", "Computer Science"],
    
    # Mechanical & Aerospace
    "Robotics": ["Mechanical", "Electronics", "Computer Science"],
    "Automation": ["Mechanical", "Electronics", "Electrical"],
    "CAD": ["Mechanical"],
    "CFD": ["Mechanical", "Aerospace"],
    "Fluid Mechanics": ["Mechanical", "Aerospace", "Chemical"],
    
    # Chemical Engineering
    "Chemical": ["Chemical"],
    "Process Engineering": ["Chemical"],
    "Thermodynamics": ["Chemical", "Mechanical"],
    "Reaction Engineering": ["Chemical"],
    
    # Materials & Metallurgy
    "Materials Science": ["Metallurgical", "Materials"],
    "Nanotechnology": ["Materials", "Chemistry", "Physics"],
    
    # Civil & Architecture
    "Structural Engineering": ["Civil"],
    "Construction": ["Civil"],
    "Architecture": ["Architecture"],
    
    # Mathematics & Physics
    "Mathematics": ["Mathematics"],
    "Statistics": ["Mathematics"],
    "Probability": ["Mathematics"],
    "Physics": ["Physics"],
    "Quantum": ["Physics", "Computer Science"],
    "Quantum Computing": ["Computer Science", "Physics"],
    
    # General technical
    "Research": ["Computer Science", "Electronics", "Electrical"],
    "Competitive Programming": ["Computer Science", "Mathematics"],
}

# Full department names for IIT KGP
DEPARTMENT_FULL_NAMES = {
    "Computer Science": ["Computer Science", "CSE", "CS"],
    "Electronics": ["Electronics", "EC", "ECE", "E&ECE"],
    "Electrical": ["Electrical", "EE"],
    "Mechanical": ["Mechanical", "ME"],
    "Chemical": ["Chemical", "CH", "Chem"],
    "Civil": ["Civil", "CE"],
    "Mathematics": ["Mathematics", "Maths", "Math"],
    "Physics": ["Physics"],
    "Chemistry": ["Chemistry", "Chem"],
    "Metallurgical": ["Metallurgical", "MT", "Materials"],
    "Aerospace": ["Aerospace", "AE"],
    "Industrial": ["Industrial", "IM", "Industrial Management"],
    "Architecture": ["Architecture", "AR"],
    "Materials": ["Materials", "Metallurgical"],
}


def recommend_departments(cv: StudentCV, max_departments: int = 5) -> List[str]:
    """
    Recommend relevant departments based on CV skills and interests.
    
    Args:
        cv: Parsed StudentCV object
        max_departments: Maximum number of departments to recommend
        
    Returns:
        List of department name keywords to filter by
    """
    department_scores: dict = {}
    
    # Get all skills from CV
    all_skills = cv.get_all_skills()
    
    # Add interests
    all_skills.extend(cv.interests)
    
    # Add project technologies
    for project in cv.projects:
        all_skills.extend(project.technologies)
    
    # Add competition/internship keywords
    for intern in cv.internships:
        if intern.objective:
            all_skills.append(intern.objective)
    
    for comp in cv.competitions:
        if comp.objective:
            all_skills.append(comp.objective)
    
    # Score departments based on skill matches
    for skill in all_skills:
        skill_lower = skill.lower()
        
        for mapped_skill, departments in SKILL_TO_DEPARTMENT_MAP.items():
            if mapped_skill.lower() in skill_lower or skill_lower in mapped_skill.lower():
                for dept in departments:
                    department_scores[dept] = department_scores.get(dept, 0) + 1
    
    # Add department from CV if mentioned
    if cv.department:
        cv_dept = cv.department.lower()
        for dept_name, aliases in DEPARTMENT_FULL_NAMES.items():
            if any(alias.lower() in cv_dept for alias in aliases):
                department_scores[dept_name] = department_scores.get(dept_name, 0) + 3
    
    # Sort by score and get top departments
    sorted_depts = sorted(department_scores.items(), key=lambda x: x[1], reverse=True)
    
    # Get department filter keywords
    recommended = []
    for dept, score in sorted_depts[:max_departments]:
        if score > 0:
            recommended.append(dept)
    
    # Default to Computer Science if no matches
    if not recommended:
        recommended = ["Computer Science"]
    
    return recommended


def get_department_filters(cv: StudentCV) -> List[str]:
    """
    Get department filter strings for faculty scraping.
    
    Returns ordered list of department codes based on CV skill matching.
    CS/EC/EE are prioritized for tech/AI profiles.
    """
    base_depts = recommend_departments(cv)
    
    # Convert to department codes, preserving priority order
    from ..tools.web_scraper import DEPARTMENT_CODES
    
    filters = []
    seen = set()
    
    for dept in base_depts:
        # Get the department code
        if dept in DEPARTMENT_CODES:
            code = DEPARTMENT_CODES[dept]
        elif dept in DEPARTMENT_CODES.values():
            code = dept
        else:
            # Try to find in aliases
            for full_name, aliases in DEPARTMENT_FULL_NAMES.items():
                if dept in aliases:
                    code = DEPARTMENT_CODES.get(full_name, dept)
                    break
            else:
                code = dept
        
        if code not in seen:
            filters.append(code)
            seen.add(code)
    
    # Default to CS if no filters
    if not filters:
        filters = ["CS"]
    
    return filters

