# AI Resume Screening & Ranking System

A small production-minded resume screening system for an SDE Intern role requiring strong Python fundamentals and practical exposure to AI/LLM/agentic systems.

The system processes a directory of PDF resumes, extracts candidate information, applies hard eligibility filters, evaluates engineering and AI project depth, enriches candidates with public GitHub activity, and produces an explainable ranked shortlist.

## Features

* Batch processing of approximately 50 PDF resumes
* Native PDF text extraction using PyMuPDF
* Structured resume extraction using Pydantic models
* Hard rule-based Python + AI/agentic eligibility filtering
* AI-assisted semantic project and engineering assessment
* Deterministic 100-point scoring
* Shallow AI-project penalties
* Public GitHub enrichment
* Per-resume failure isolation
* Machine-readable JSON output
* CLI-first interface

## Architecture

```text
PDF Resumes
    |
    v
PyMuPDF
    |
    v
ResumeData
    |
    v
Hard Eligibility Filter
    |
    +---- Rejected --------------------+
    |                                  |
    |                                  v
    |                            ScreeningResult
    |
    +---- Eligible
            |
            v
      CandidateAssessment
            |
            v
       GitHub Enrichment
            |
            v
       Python Scoring
            |
            v
       ScreeningResult
            |
            v
        Ranked JSON
```

## Project Structure

```text
.
├── app/
│   ├── main.py
│   ├── pipeline.py
│   ├── config.py
│   ├── output.py
│   │
│   ├── models/
│   │   ├── resume.py
│   │   ├── assessment.py
│   │   └── result.py
│   │
│   ├── parsers/
│   │   └── pdf.py
│   │
│   ├── extraction/
│   │   ├── resume_extractor.py
│   │   └── resume_assessor.py
│   │
│   ├── screening/
│   │   ├── eligibility.py
│   │   └── scorer.py
│   │
│   └── enrichment/
│       └── github.py
│
├── resumes/
├── output/
├── tests/
├── .env.example
├── .gitignore
├── pyproject.toml
└── uv.lock
```

## Requirements

* Python 3.12+
* `uv`
* PDF resumes in the input directory

## Setup

Install dependencies:

```bash
uv sync
```

Create a `.env` file in the project root.

### Development / no API credits

```env
SCREENING_MODE=fallback

OPENAI_API_KEY=
OPENAI_MODEL=gpt-5-mini

GITHUB_TOKEN=
```

### AI-assisted mode

```env
SCREENING_MODE=llm

OPENAI_API_KEY=your_api_key
OPENAI_MODEL=gpt-5-mini

GITHUB_TOKEN=optional_github_token
```

`SCREENING_MODE=auto` can also be used:

```env
SCREENING_MODE=auto
OPENAI_API_KEY=your_api_key
```

In `auto` mode the application uses the LLM when credentials are available and falls back to deterministic processing otherwise.

Never commit `.env` or real API keys.

## Running

Process the resume directory:

```bash
uv run python -m app.main \
  --input ./resumes \
  --output ./output/results.json
```

Example:

```text
Processed: 50 | Eligible: 39 | Rejected: 11 | Failed: 0
```

## Eligibility Rules

Eligibility is intentionally rule-based and happens before ranking.

A candidate must satisfy both:

### Python evidence

Python must appear as a genuine skill, project technology, work/internship technology, or implementation language.

### AI / Agentic evidence

The resume must contain meaningful AI/LLM/RAG/agentic implementation evidence such as:

* LangChain
* LangGraph
* Google ADK
* LlamaIndex
* RAG
* embeddings
* vector search / vector databases
* tool-calling agents
* multi-agent workflows
* evaluation pipelines
* equivalent custom implementations

A candidate is not rejected simply because JavaScript, Java, React, or Next.js is also present.

## Scoring

Eligible candidates are scored out of 100 points.

| Category                         |  Weight |
| -------------------------------- | ------: |
| AI / Agentic / RAG Project Depth |      40 |
| Python & Backend Engineering     |      30 |
| Cloud / Deployment / Full Stack  |      15 |
| GitHub Activity                  |      10 |
| Engineering Depth Signals        |       5 |
| **Total**                        | **100** |

The system can apply a 5–15 point penalty to shallow AI projects, particularly projects that are primarily thin wrappers around an LLM/API without meaningful workflow, retrieval, state management, backend logic, evaluation, or product logic.

The final arithmetic is performed in Python after semantic assessment rather than trusting an LLM to calculate the final score.

## AI / LLM Usage

The application uses a hybrid approach.

### LLM responsibilities

The LLM is used for:

1. Structured resume information extraction
2. Semantic assessment of AI project depth and engineering depth
3. Evidence-backed strengths, concerns, and project summaries

LLM outputs are constrained using Pydantic structured schemas.

### Python responsibilities

Python handles:

1. Hard eligibility filtering
2. Score calculation
3. Score bounds and penalties
4. Ranking
5. Batch orchestration
6. Error handling

This keeps the system predictable and testable.

## GitHub Enrichment

When a GitHub profile is found in a resume, the system uses the public GitHub API to collect lightweight engineering signals.

The GitHub score is capped at 10 points:

* Recent public engineering activity: 0–5
* Relevant maintained repositories: 0–5

GitHub is an additional positive signal and is not a hard eligibility requirement.

If a profile is missing, private, unavailable, or the API is rate-limited, screening continues and the candidate receives a zero GitHub score with an explicit enrichment status.

## Output

The application generates:

```text
output/results.json
```

The output includes:

* Candidate name
* Eligibility status
* Rank
* Final score
* Score breakdown
* Matched skills
* Project summary
* Strengths
* Concerns
* Eligibility evidence
* GitHub enrichment status and summary
* Batch summary

Example:

```json
{
  "summary": {
    "total_resumes": 50,
    "successfully_parsed": 50,
    "eligible": 39,
    "rejected": 11,
    "failed": 0
  },
  "candidates": [
    {
      "rank": 1,
      "candidate_name": "Candidate Name",
      "eligible": true,
      "score": {
        "ai_project_depth": 35,
        "python_backend": 27,
        "cloud_fullstack": 12,
        "engineering_depth": 4,
        "github": 8,
        "total": 86
      }
    }
  ]
}
```

## Error Handling

A failure for one resume does not terminate the batch.

The pipeline handles:

* Malformed or unreadable PDFs
* Missing candidate fields
* LLM/API failures
* Missing GitHub profiles
* GitHub API failures
* GitHub rate limits

Failed candidates are recorded in the output with an explicit reason.

## Design Decisions

### Why PyMuPDF?

The assignment requires PDF support and the provided resumes can have different layouts. PyMuPDF provides fast native PDF text extraction while keeping the implementation lightweight.

OCR was intentionally not included because it is not required by the assignment and would add complexity to the constrained implementation window.

### Why hard eligibility before AI scoring?

The minimum Python + AI requirement is a hard filter. This prevents a well-written but irrelevant resume from receiving a high ranking simply because it contains other strong technologies.

### Why hybrid scoring?

LLMs are useful for understanding project depth and implementation quality, but deterministic Python is better suited for final arithmetic, score limits, penalties, and ranking.

### Why JSON?

JSON makes the output machine-readable while still allowing detailed evidence, score breakdowns, and GitHub status.

### Why no database?

The assignment explicitly allows JSON/CSV output and does not require persistent storage.

### Why no frontend?

The assignment prioritizes backend correctness, explainability, and engineering judgment. A CLI is sufficient.

## Testing

Run static compilation checks:

```bash
uv run python -m compileall app
```

Import-check the pipeline:

```bash
uv run python -c \
"from app.pipeline import screen_resumes; print('pipeline OK')"
```

Run tests when implemented:

```bash
uv run pytest
```

The most important tests cover eligibility and scoring logic.

## If I Had More Time

1. Improve resume section detection and extraction for highly varied PDF layouts.
2. Add stronger evaluation of project ownership and implementation evidence.
3. Add bounded asynchronous processing for LLM and GitHub requests.
4. Add caching for LLM/GitHub responses and a small HTML/terminal report.

## Scope

This implementation intentionally does not include:

* Frontend
* Authentication
* Database
* Vector database
* Deployment infrastructure
* OCR
* Microservices

These are outside the required scope for the assignment's 2–3 hour implementation window.

## License

For assignment / evaluation use.
