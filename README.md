# Internship Agent System

A multi-agent system for automated, personalized internship outreach to IIT Kharagpur professors.

## Features

- **Faculty Scraping**: Automated extraction of professor data from IIT KGP website
- **Research Enrichment**: Web search and Google Scholar integration for research data
- **CV Parsing**: Structured extraction from PDF/DOCX resumes
- **Personalized Outreach**: AI-generated cold emails and cover letters

## Quick Start

```bash
# Clone and setup
cd internship-agent
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
playwright install chromium

# Configure environment
cp .env.example .env
# Edit .env with your API keys

# Run the pipeline
python -m src.main
```

## API Usage

```bash
uvicorn api.main:app --reload
# Visit http://localhost:8000/docs for API documentation
```

## Project Structure

```
src/
├── agents/         # Agent implementations
├── graph/          # LangGraph workflow
├── schemas/        # Pydantic data models
├── tools/          # Scraping & parsing utilities
└── utils/          # Configuration & logging
```

## License

MIT
