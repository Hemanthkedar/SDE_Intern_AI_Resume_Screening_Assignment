import os

from openai import OpenAI

from app.config import OPENAI_MODEL, SCREENING_MODE
from app.models.assessment import CandidateAssessment
from app.models.resume import ResumeData


SYSTEM_PROMPT = """
You are an expert technical recruiter evaluating candidates for an
SDE internship focused on Python and practical AI/agentic systems.

Score using:

- AI / Agentic / RAG Project Depth: 0-40
- Python & Backend Engineering: 0-30
- Cloud / Deployment / Full Stack: 0-15
- Engineering Depth: 0-5

Reward concrete implementation evidence over keyword-only skills.

Strong AI evidence includes:
- agents
- RAG
- retrieval
- embeddings
- vector search
- tool calling
- orchestration
- state management
- evaluation
- meaningful backend/business logic

Penalize shallow AI projects that are primarily API wrappers with
little workflow, retrieval, state, backend logic, evaluation, or
product logic.

Penalize tutorial-style projects when implementation ownership is
unclear.

Do not invent experience or technologies.

Return concise evidence, strengths, and concerns.
"""


class ResumeAssessor:
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

    def assess(
        self,
        resume: ResumeData,
    ) -> CandidateAssessment:
        if self.client is not None:
            return self._assess_with_llm(resume)

        return self._assess_fallback(resume)

    def _assess_with_llm(
        self,
        resume: ResumeData,
    ) -> CandidateAssessment:
        response = self.client.responses.parse(
            model=OPENAI_MODEL,
            input=[
                {
                    "role": "system",
                    "content": SYSTEM_PROMPT,
                },
                {
                    "role": "user",
                    "content": resume.model_dump_json(),
                },
            ],
            text_format=CandidateAssessment,
        )

        if response.output_parsed is None:
            raise ValueError(
                "LLM returned no candidate assessment"
            )

        return response.output_parsed

    @staticmethod
    def _assess_fallback(
        resume: ResumeData,
    ) -> CandidateAssessment:
        text = resume.raw_text.lower()

        ai_signals = {
            "langchain",
            "langgraph",
            "rag",
            "embeddings",
            "vector search",
            "vector database",
            "tool calling",
            "multi-agent",
            "agentic",
            "llamaindex",
        }

        python_signals = {
            "python",
            "fastapi",
            "django",
            "flask",
            "postgresql",
            "postgres",
            "redis",
            "async",
        }

        cloud_signals = {
            "docker",
            "gcp",
            "google cloud",
            "deployment",
            "deployed",
            "react",
            "next.js",
            "nextjs",
        }

        engineering_signals = {
            "pytest",
            "testing",
            "caching",
            "queue",
            "concurrency",
            "observability",
            "logging",
            "retry",
        }

        matched_ai = [
            signal
            for signal in ai_signals
            if signal in text
        ]

        matched_python = [
            signal
            for signal in python_signals
            if signal in text
        ]

        matched_cloud = [
            signal
            for signal in cloud_signals
            if signal in text
        ]

        matched_engineering = [
            signal
            for signal in engineering_signals
            if signal in text
        ]

        ai_score = min(
            len(matched_ai) * 5,
            40,
        )

        python_score = min(
            len(matched_python) * 4,
            30,
        )

        cloud_score = min(
            len(matched_cloud) * 3,
            15,
        )

        engineering_score = min(
            len(matched_engineering),
            5,
        )

        shallow = (
            len(matched_ai) <= 1
            and any(
                term in text
                for term in (
                    "openai api",
                    "llm api",
                    "chatbot",
                )
            )
        )

        penalty = 10 if shallow else 0

        evidence: list[str] = []

        for project in resume.projects:
            evidence.extend(project.evidence)

        if not evidence:
            evidence = matched_ai + matched_python

        return CandidateAssessment(
            ai_project_depth=ai_score,
            python_backend_depth=python_score,
            cloud_fullstack_depth=cloud_score,
            engineering_depth=engineering_score,
            shallow_ai_project=shallow,
            shallow_project_penalty=penalty,
            project_summary=(
                "Fallback assessment based on detected "
                "resume signals."
            ),
            strengths=[
                f"Detected: {signal}"
                for signal in (
                    matched_ai
                    + matched_python
                    + matched_cloud
                )[:6]
            ],
            concerns=(
                ["Limited project-depth evidence"]
                if shallow
                else []
            ),
            evidence=evidence[:10],
        )