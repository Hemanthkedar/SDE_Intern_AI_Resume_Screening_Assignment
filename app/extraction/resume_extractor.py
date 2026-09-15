import os

from openai import OpenAI

from app.models.resume import ResumeData
from app.config import OPENAI_MODEL

SYSTEM_PROMPT = """
You are a resume information extraction system.

Extract only information that is explicitly supported by the resume.
Do not invent skills, technologies, companies, projects, or experience.

Important:
- Preserve meaningful project implementation details.
- Distinguish actual project/experience usage from a generic skills list.
- Extract a GitHub URL when one is present.
- For project evidence, capture concrete implementation details such as:
  RAG, retrieval, embeddings, vector databases, agents, tool calling,
  orchestration, state management, evaluation, APIs, backend systems,
  caching, queues, deployment, testing, etc.
"""


class ResumeExtractor:
    def __init__(self, client: OpenAI | None = None):
        self.client = client or OpenAI(
            api_key=os.environ["OPENAI_API_KEY"]
        )

    def extract(self, resume_text: str) -> ResumeData:
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
            raise ValueError("LLM returned no structured resume data")

        result = response.output_parsed
        result.raw_text = resume_text

        return result