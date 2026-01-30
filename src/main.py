"""
Internship Agent System - Main Entry Point

Run the full agent pipeline from command line.
"""

import asyncio
import argparse
import json
from pathlib import Path

from src.graph.workflow import run_pipeline
from src.utils.config import settings
from src.utils.logger import get_logger

logger = get_logger(__name__)


async def main():
    """Main entry point for CLI execution."""
    parser = argparse.ArgumentParser(
        description="Internship Agent System - Automated outreach to IIT KGP professors"
    )
    
    parser.add_argument(
        "--cv",
        type=str,
        help="Path to student CV file (PDF or DOCX)"
    )
    
    parser.add_argument(
        "--departments",
        type=str,
        nargs="+",
        help="Filter by departments (e.g., 'Computer Science' 'Aerospace')"
    )
    
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Maximum number of faculty to scrape"
    )
    
    parser.add_argument(
        "--min-score",
        type=float,
        default=0.3,
        help="Minimum match score for email generation (0.0-1.0)"
    )
    
    parser.add_argument(
        "--mode",
        type=str,
        choices=["full", "scrape_only", "cv_only"],
        default="full",
        help="Pipeline mode"
    )
    
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Output file for generated emails (JSON)"
    )
    
    args = parser.parse_args()
    
    # Validate CV path if provided
    if args.cv:
        cv_path = Path(args.cv)
        if not cv_path.exists():
            logger.error(f"CV file not found: {args.cv}")
            return
        args.cv = str(cv_path.absolute())
    
    # Run pipeline
    logger.info("Starting Internship Agent Pipeline")
    logger.info(f"Mode: {args.mode}")
    if args.departments:
        logger.info(f"Departments: {args.departments}")
    if args.limit:
        logger.info(f"Faculty limit: {args.limit}")
    
    try:
        final_state = await run_pipeline(
            cv_path=args.cv,
            target_departments=args.departments,
            faculty_limit=args.limit,
            min_match_score=args.min_score,
            workflow_type=args.mode
        )
        
        # Print summary
        print("\n" + "=" * 60)
        print("PIPELINE COMPLETE")
        print("=" * 60)
        
        print(f"\nCompleted Steps: {final_state.get('completed_steps', [])}")
        print(f"Faculty Scraped: {len(final_state.get('faculty_profiles', []))}")
        print(f"Profiles Enriched: {len(final_state.get('enriched_profiles', []))}")
        
        if final_state.get('student_cv'):
            print(f"CV Parsed: {final_state['student_cv'].student_name}")
        
        email_outputs = final_state.get('email_outputs', [])
        print(f"Emails Generated: {len(email_outputs)}")
        
        if final_state.get('errors'):
            print(f"\nErrors: {final_state['errors']}")
        
        # Save outputs
        if email_outputs:
            output_path = args.output or str(
                settings.output_dir / "generated_emails.json"
            )
            
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(
                    [o.model_dump() for o in email_outputs],
                    f,
                    indent=2,
                    ensure_ascii=False
                )
            
            print(f"\nEmails saved to: {output_path}")
            
            # Print sample email
            if email_outputs:
                print("\n" + "-" * 60)
                print("SAMPLE EMAIL (Top Match)")
                print("-" * 60)
                top = email_outputs[0]
                print(f"To: Professor {top.professor_name}")
                print(f"Department: {top.department}")
                print(f"Match Score: {top.overall_match_score:.2f}")
                print(f"\nSubject: {top.email_subject}")
                print(f"\n{top.email_body}")
        
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
