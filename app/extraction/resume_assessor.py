import json
import os

from openai import OpenAI

from app.models.assessment import CandidateAssessment
from app.models.resume import ResumeData
from app.config import OPENAI_MODEL


SYSTEM_PROMPT = """
You are an expert technical recruiter evaluating candidates for an
SDE internship focused on Python and practical AI/agentic systems.

Evaluate ONLY evidence contained in the supplied resume.

Scoring baseline:
- AI / Agentic / RAG Project Depth: 0-40
- Python & Backend Engineering: 0-30
- Cloud / Deployment / Full Stack: 0-15
- Engineering Depth: 0-5

Important rules:
1. Reward concrete implementation evidence over keyword-only skills.
2. Strong AI evidence includes agents, RAG, retrieval, embeddings,
   vector search, tool calling, orchestration, state management,
   evaluation, and meaningful backend/business logic.
3. Penalize shallow projects that are mainly an LLM/API wrapper with
   little implementation depth.
4. Penalize tutorial-style projects when ownership or implementation
   details are unclear.
5. Do not invent experience or technologies.
6. Every important judgment should be supported by concise evidence.
7. Do not evaluate GitHub here. GitHub is handled separately.
"""


class ResumeAssessor:
    def __init__(self, client: OpenAI | None = None):
        self.client = client or OpenAI(
            api_key=os.environ["OPENAI_API_KEY"]
        )

    def assess(self, resume: ResumeData) -> CandidateAssessment:
        candidate_data = {
            "candidate_name": resume.candidate_name,
            "skills": resume.skills,
            "education": resume.education,
            "experience": [
                experience.model_dump()
                for experience in resume.experience
            ],
            "projects": [
                project.model_dump()
                for project in resume.projects
            ],
        }

        response = self.client.responses.parse(
            model=OPENAI_MODEL,
            input=[
                {
                    "role": "system",
                    "content": SYSTEM_PROMPT,
                },
                {
                    "role": "user",
                    "content": json.dumps(candidate_data),
                },
            ],
            text_format=CandidateAssessment,
        )

        if response.output_parsed is None:
            raise ValueError(
                "LLM returned no structured candidate assessment"
            )

        return response.output_parsed