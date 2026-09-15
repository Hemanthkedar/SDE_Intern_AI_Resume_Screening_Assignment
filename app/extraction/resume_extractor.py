import os
import re

from openai import OpenAI

from app.config import OPENAI_MODEL, SCREENING_MODE
from app.models.resume import Experience, Project, ResumeData


SYSTEM_PROMPT = """
You are a resume information extraction system.

Extract only information explicitly supported by the resume.
Do not invent skills, technologies, companies, projects, or experience.

Preserve concrete project implementation details and extract:
- candidate name
- email
- phone
- skills
- education
- experience
- projects
- GitHub URL
- project evidence
"""


class ResumeExtractor:
    def __init__(self, client: OpenAI | None = None):
        self.client = client

        if SCREENING_MODE not in {"auto", "llm", "fallback"}:
            raise ValueError(
                "SCREENING_MODE must be one of: auto, llm, fallback"
            )

        if self.client is not None:
            return

        if SCREENING_MODE == "fallback":
            return

        if SCREENING_MODE == "llm":
            if not os.getenv("OPENAI_API_KEY"):
                raise RuntimeError(
                    "SCREENING_MODE=llm requires OPENAI_API_KEY"
                )

            self.client = OpenAI(
                api_key=os.environ["OPENAI_API_KEY"],
                timeout=30.0,
                max_retries=1,
            )
            return

        # auto mode
        if os.getenv("OPENAI_API_KEY"):
            self.client = OpenAI(
                api_key=os.environ["OPENAI_API_KEY"],
                timeout=30.0,
                max_retries=1,
            )

    def extract(self, resume_text: str) -> ResumeData:
        if self.client is not None:
            return self._extract_with_llm(resume_text)

        return self._extract_fallback(resume_text)

    def _extract_with_llm(self, resume_text: str) -> ResumeData:
        response = self.client.responses.parse(
            model=OPENAI_MODEL,
            input=[
                {
                    "role": "system",
                    "content": SYSTEM_PROMPT,
                },
                {
                    "role": "user",
                    "content": resume_text,
                },
            ],
            text_format=ResumeData,
        )

        if response.output_parsed is None:
            raise ValueError(
                "LLM returned no structured resume data"
            )

        result = response.output_parsed
        result.raw_text = resume_text

        return result

    @staticmethod
    def _extract_fallback(resume_text: str) -> ResumeData:
        text = resume_text.strip()

        lines = [
            line.strip()
            for line in text.splitlines()
            if line.strip()
        ]

        email_match = re.search(
            r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}",
            text,
        )

        github_match = re.search(
            r"https?://(?:www\.)?github\.com/[A-Za-z0-9_.-]+",
            text,
            re.IGNORECASE,
        )

        phone_match = re.search(
            r"(?<!\d)(?:\+?\d[\d\s().-]{8,}\d)(?!\d)",
            text,
        )

        # Best-effort candidate name.
        candidate_name = None

        for line in lines[:10]:
            if (
                "@" not in line
                and "github.com" not in line.lower()
                and not re.search(r"\d{5,}", line)
                and len(line.split()) <= 5
            ):
                candidate_name = line
                break

        known_signals = {
            "python",
            "fastapi",
            "django",
            "flask",
            "pandas",
            "numpy",
            "postgresql",
            "postgres",
            "redis",
            "docker",
            "gcp",
            "react",
            "next.js",
            "nextjs",
            "langchain",
            "langgraph",
            "llamaindex",
            "rag",
            "embeddings",
            "vector search",
            "vector database",
            "tool calling",
            "multi-agent",
            "agentic",
        }

        lower_text = text.lower()

        skills = sorted(
            signal
            for signal in known_signals
            if signal in lower_text
        )

        projects: list[Project] = []

        project_keywords = (
            "project",
            "built",
            "developed",
            "implemented",
            "created",
        )

        for line in lines:
            lower_line = line.lower()

            if any(
                keyword in lower_line
                for keyword in project_keywords
            ):
                projects.append(
                    Project(
                        name="Resume Project",
                        description=line,
                        technologies=[
                            skill
                            for skill in skills
                            if skill in lower_line
                        ],
                        evidence=[line],
                    )
                )

        return ResumeData(
            candidate_name=candidate_name,
            email=(
                email_match.group(0)
                if email_match
                else None
            ),
            phone=(
                phone_match.group(0)
                if phone_match
                else None
            ),
            skills=skills,
            education=[],
            experience=[],
            projects=projects,
            github_url=(
                github_match.group(0)
                if github_match
                else None
            ),
            raw_text=text,
        )