#  IIT KGP Internship Agent

An AI-powered multi-agent pipeline that automates personalized research internship outreach for IIT Kharagpur students.

##  Features

- ** CV Parsing**: Extracts skills, projects, interests from PDF/DOCX CVs using GPT-4o
- ** Faculty Scraping**: Scrapes 188+ faculty profiles from IIT KGP website with real emails
- ** Intelligent Matching**: Auto-selects relevant departments (CS, EC, EE) based on your CV
- ** Research Enrichment**: Uses Serper API to find professor publications & research areas
- ** Personalized Emails**: Generates tailored outreach emails with match scores (0.0-1.0)
- ** Cover Letters**: Creates professional cover letters for each professor

##  Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                        LangGraph Workflow                            │
├─────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────────────┐   │
│  │   Parse CV   │───►│ Recommend    │───►│   Scrape Faculty     │   │
│  │   (GPT-4o)   │    │ Departments  │    │   (Playwright)       │   │
│  └──────────────┘    └──────────────┘    └──────────┬───────────┘   │
│                                                      │               │
│                                                      ▼               │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │                    Enrich Profiles                            │   │
│  │                    (Serper API)                               │   │
│  └──────────────────────────────────────┬───────────────────────┘   │
│                                          │                           │
│                                          ▼                           │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │               Generate Personalized Emails                    │   │
│  │                       (GPT-4o)                                │   │
│  └──────────────────────────────────────────────────────────────┘   │
│                                                                       │
└─────────────────────────────────────────────────────────────────────┘
```

##  Quick Start

### 1. Clone & Install

```bash
git clone <repo-url>
cd devsoc
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
playwright install chromium
```

### 2. Configure API Keys

```bash
cp .env.example .env
# Edit .env with your keys:
# - OPENAI_API_KEY (required)
# - SERPER_API_KEY (free tier: 2500/month at serper.dev)
```

### 3. Run Pipeline

```bash
# Basic run with 10 professors
python -m src.main --cv your_cv.pdf --limit 10

# Target specific department
python -m src.main --cv your_cv.pdf --departments "Computer Science" --limit 20

# Set minimum match score
python -m src.main --cv your_cv.pdf --limit 15 --min-score 0.3
```

##  Project Structure

```
devsoc/
├── src/
│   ├── agents/                 # AI Agents
│   │   ├── cv_parser.py        # Agent 1: CV Parsing
│   │   ├── faculty_scraper.py  # Agent 2: Faculty Scraping
│   │   ├── research_enrichment.py  # Agent 3: Research Enrichment
│   │   └── personalization.py  # Agent 4: Email Generation
│   │
│   ├── tools/                  # Agent Tools
│   │   ├── document_parser.py  # PDF/DOCX extraction
│   │   ├── web_scraper.py      # Playwright scraper
│   │   └── search_tool.py      # Serper API integration
│   │
│   ├── graph/                  # LangGraph Workflow
│   │   ├── workflow.py         # Node definitions & edges
│   │   └── state.py            # TypedDict state schema
│   │
│   ├── schemas/                # Pydantic Models
│   │   ├── cv.py               # StudentCV, Project, etc.
│   │   ├── faculty.py          # FacultyProfile
│   │   ├── research.py         # EnrichedProfile
│   │   └── output.py           # EmailOutput
│   │
│   ├── utils/                  # Utilities
│   │   ├── config.py           # Pydantic Settings
│   │   ├── logger.py           # Structured logging
│   │   └── department_recommender.py  # CV → Department mapping
│   │
│   └── main.py                 # CLI entry point
│
├── data/
│   ├── raw/                    # Scraped faculty profiles
│   ├── enriched/               # Enriched with research data
│   └── outputs/                # Generated emails (JSON)
│
├── requirements.txt
├── .env.example
└── ARCHITECTURE.md             # Detailed architecture docs
```

##  Configuration

| Environment Variable | Description | Required |
|---------------------|-------------|----------|
| `OPENAI_API_KEY` | OpenAI API key for GPT-4o |  Yes |
| `SERPER_API_KEY` | Serper.dev API key (free tier) |  Yes |
| `SCRAPER_DELAY` | Delay between requests (default: 2.0s) |  No |
| `LLM_MODEL` | OpenAI model (default: gpt-4o) |  No |
| `LOG_LEVEL` | Logging level (default: INFO) |  No |

##  Sample Output

```json
{
  "professor_name": "Abhijnan Chakraborty",
  "professor_email": "abhijnan@cse.iitkgp.ac.in",
  "department": "CS",
  "match_reasons": ["AI research", "DeepFake detection"],
  "overall_match_score": 0.65,
  "email_subject": "Research Internship Inquiry - AI-Powered Platforms",
  "email_body": "Dear Professor Chakraborty,\n\n..."
}
```

##  How It Works

### 1. CV Parsing
- Extracts text from PDF/DOCX using PyMuPDF/python-docx
- GPT-4o structures data into: skills, projects, internships, interests
- Identifies relevant departments based on skills (ML → CS, VLSI → EC)

### 2. Faculty Scraping
- Navigates to department pages (`/department/CS`, `/department/EC`)
- Selects "Faculty" from dropdown, waits for dynamic content
- Extracts: name, email, designation, research areas, profile URL

### 3. Research Enrichment
- Searches Google via Serper API for each professor
- Queries: general info, publications, Google Scholar
- Enhances profiles with recent research, publications

### 4. Email Generation
- Calculates match score based on CV ↔ Professor overlap
- GPT-4o generates personalized email referencing:
  - Specific professor research areas
  - Student's relevant projects
  - Common interests/technologies

##  Performance

| Metric | Value |
|--------|-------|
| Departments scraped | 5 (CS, EC, EE, MA, CH) |
| Faculty profiles | 188 total |
| Serper searches/prof | 3 queries |
| Email generation | ~15s per email |
| Avg match score | 0.55 - 0.70 |

##  Development

```bash
# Run tests
pytest tests/

# Format code
black src/

# Type checking
mypy src/
```

##  License

MIT License - Built for DevSoC IIT Kharagpur

##  Credits

- **LangGraph** - Agent orchestration framework
- **Playwright** - Web scraping
- **Serper.dev** - Google Search API
- **OpenAI** - GPT-4o for NLU/NLG
