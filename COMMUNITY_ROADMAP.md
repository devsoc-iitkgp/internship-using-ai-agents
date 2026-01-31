# Developers' Society: Project Roadmap & Contribution Guide

Welcome to the **Developers' Society** Open Source Initiative!

This project is open-sourced to allow the community to build upon the concepts covered in our **AI Agents Workshop**. Our goal is to make this tool accessible to every student while providing a sandbox for you to apply your learnings and improve your software engineering skills.

Whether you're here to fix a bug, add a feature, or just experiment with LangGraph, you are welcome! We have outlined a roadmap of **standalone features** tailored to different skill levels, so you can contribute regardless of your experience.

---

## Feature 1: The "Human-in-the-Loop" Dashboard
**Difficulty:** 🟢 Beginner / Intermediate
**Tech Stack:** Python, Streamlit (recommended) or React

### The Goal
Currently, the system generates email drafts as JSON data. We need a user interface (UI) where a student can:
1. Upload their CV.
2. Select target departments.
3. **Review** the generated email drafts.
4. **Edit** the drafts if the AI made a mistake.
5. Click **"Approve & Send"** (or "Save").

### Implementation Roadmap
1.  **Setup Streamlit:** Create a new folder `src/ui/` and a file `app.py`.
2.  **Connect to API:** Use the `requests` library to hit the FastAPI endpoints (`localhost:8000/cv/upload`, `/generate`).
3.  **Build the Review Page:**
    *   Display the generated emails in a list.
    *   Use `st.text_area` to allow the user to edit the Subject and Body.
    *   Add an "Approve" button that saves the final text to a file or database.
4.  **Visuals:** Display the "Match Score" using a progress bar or color code (Green for high match, Red for low).

### Files to Touch
*   Create: `src/ui/app.py`
*   Read: `api/main.py` (to understand endpoints)

---

## Feature 2: Email Dispatcher Service
**Difficulty:** 🟡 Intermediate
**Tech Stack:** Python, SMTP, Gmail API (optional)

### The Goal
The system generates text, but it can't send emails yet. We need a secure module to send the approved drafts. **Crucially**, it must have a "Safety Mode" to prevent accidental spam.

### Implementation Roadmap
1.  **Create the Tool:** Create `src/tools/email_sender.py`.
2.  **Implement SMTP:** Use Python's built-in `smtplib`.
    *   Load credentials (`EMAIL_USER`, `EMAIL_PASSWORD`) from `.env`.
3.  **Safety First (Dry Run):** Implement a flag `dry_run=True`.
    *   If `True`: Log the email to the console or send it to *yourself*.
    *   If `False`: Send it to the actual professor.
4.  **Rate Limiting:** Ensure the script sleeps for 30-60 seconds between emails to avoid getting blocked by email providers.
5.  **API Endpoint:** Add a `/send` endpoint in `api/main.py` that takes an `email_id` and triggers the sender.

### Files to Touch
*   Create: `src/tools/email_sender.py`
*   Modify: `api/main.py`

---

## Feature 3: Database Persistence
**Difficulty:** 🟡 Intermediate
**Tech Stack:** Python, SQLModel (or SQLAlchemy), SQLite

### The Goal
Currently, if the server restarts, all parsed CVs and generated drafts are lost (they are stored in memory). We need a proper database to save the state of applications.

### Implementation Roadmap
1.  **Define Models:** Create `src/database/models.py`.
    *   `Student` (Name, Email, CV path)
    *   `Professor` (Name, Email, Research Areas)
    *   `Application` (Foreign Keys to Student/Professor, Status: "Draft", "Approved", "Sent", Email Body).
2.  **Setup DB Engine:** Create `src/database/engine.py` using **SQLModel** (easiest with FastAPI) and SQLite (`internship.db`).
3.  **Migrate API:** Update `api/main.py` to:
    *   Save uploaded CVs to the DB.
    *   Save generated drafts to the DB with status "Pending".
    *   Fetch drafts from DB for the UI.

### Files to Touch
*   Create: `src/database/`
*   Modify: `api/main.py`

---

## Feature 4: Multi-University Support
**Difficulty:** Advanced
**Tech Stack:** Python, Playwright, Object-Oriented Programming

### The Goal
The current scraper (`src/agents/faculty_scraper.py`) is hardcoded for **IIT Kharagpur**. We want to make the system modular so people can add support for IIT Bombay, MIT, Stanford, etc.

### Implementation Roadmap
1.  **Abstract Base Class:** Create a `BaseScraper` class in `src/tools/base_scraper.py` that defines methods like `get_faculty_list()` and `get_profile_details()`.
2.  **Refactor IIT KGP:** Move the existing logic into `IITKGPScraper` that inherits from `BaseScraper`.
3.  **Implement New University:** Create a new scraper (e.g., `IITBombayScraper`) that implements the base methods for a different website structure.
4.  **Factory Pattern:** specific a `ScraperFactory` that returns the correct scraper based on a configuration string (e.g., "IIT_KGP" or "IIT_B").

### Files to Touch
*   Modify: `src/tools/web_scraper.py`
*   Modify: `src/agents/faculty_scraper.py`

---

## Feature 5: Local LLM Support (Ollama / Llama.cpp)
**Difficulty:** 🟡 Intermediate
**Tech Stack:** Python, LangChain, Ollama

### The Goal
Using OpenAI API keys costs money. We want to support running local models (like Llama 3 or Mistral) using **Ollama** so students can use this tool for free.

### Implementation Roadmap
1.  **Config Update:** Add `LLM_PROVIDER` ("openai" or "ollama") to `src/utils/config.py`.
2.  **LLM Factory:** Create a helper function `get_llm()` that returns either `ChatOpenAI` or `ChatOllama` based on the config.
3.  **Prompt Tuning:** Local models might not follow complex JSON instructions as well as GPT-4.
    *   Test the `CVParserAgent` with Llama 3.
    *   If it fails, simplify the prompts in `src/agents/cv_parser.py`.

### Files to Touch
*   Modify: `src/utils/config.py`
*   Modify: `src/agents/*.py` (Replace direct `ChatOpenAI` calls with your new factory)

---

## How to Contribute

1.  **Fork** the repository.
2.  **Pick a feature** from the roadmap above.
3.  Create a branch: `git checkout -b feature/your-feature-name`.
4.  Implement the feature (feel free to ask questions!).
5.  **Test it** (Add tests in `tests/` if possible!).
6.  Open a **Pull Request (PR)** describing what you did and what you learned.

This project belongs to the community. Let's build something amazing together!

**Developers' Society**