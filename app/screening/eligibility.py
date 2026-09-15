from app.models.resume import ResumeData
from app.models.result import EligibilityResult


PYTHON_SIGNALS = {
    "python",
    "fastapi",
    "django",
    "flask",
    "pytest",
    "pydantic",
    "pandas",
    "numpy",
    "sqlalchemy",
    "asyncio",
}


# Signals strong enough to satisfy the hard AI/agentic requirement.
STRONG_AI_SIGNALS = {
    "langchain",
    "langgraph",
    "google adk",
    "llamaindex",
    "llama index",
    "rag",
    "retrieval augmented generation",
    "embeddings",
    "vector search",
    "vector database",
    "vector db",
    "tool calling",
    "tool-calling",
    "multi-agent",
    "multi agent",
    "agentic",
    "ai agent",
    "evaluation pipeline",
}


# These are useful later for scoring/assessment but should not
# independently satisfy the hard AI requirement.
WEAK_AI_SIGNALS = {
    "llm",
    "large language model",
    "generative ai",
    "generative ai",
    "machine learning",
}


def _normalise(value: str) -> str:
    return " ".join(value.lower().split())


def _find_signals(text: str, signals: set[str]) -> list[str]:
    normalised = _normalise(text)

    return sorted(
        signal
        for signal in signals
        if signal in normalised
    )


def _build_search_text(resume: ResumeData) -> str:
    parts = [
        " ".join(resume.skills),
        " ".join(resume.education),
    ]

    for experience in resume.experience:
        parts.extend(
            [
                experience.role,
                experience.description,
                " ".join(experience.technologies),
            ]
        )

    for project in resume.projects:
        parts.extend(
            [
                project.name,
                project.description,
                " ".join(project.technologies),
                " ".join(project.evidence),
            ]
        )

    return "\n".join(parts)


def check_eligibility(resume: ResumeData) -> EligibilityResult:
    search_text = _build_search_text(resume)

    python_evidence = _find_signals(
        search_text,
        PYTHON_SIGNALS,
    )

    ai_evidence = _find_signals(
        search_text,
        STRONG_AI_SIGNALS,
    )

    # Weak AI terms are retained as useful evidence for diagnostics,
    # but do not independently satisfy the hard gate.
    weak_ai_evidence = _find_signals(
        search_text,
        WEAK_AI_SIGNALS,
    )

    rejection_reasons: list[str] = []

    if not python_evidence:
        rejection_reasons.append(
            "No evidence of Python stack"
        )

    if not ai_evidence:
        if weak_ai_evidence:
            rejection_reasons.append(
                "AI/LLM terms found, but no meaningful AI/agentic implementation evidence"
            )
        else:
            rejection_reasons.append(
                "No AI/agentic project or implementation evidence"
            )

    return EligibilityResult(
        eligible=not rejection_reasons,
        python_evidence=python_evidence,
        ai_evidence=ai_evidence,
        rejection_reasons=rejection_reasons,
    )