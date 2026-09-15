from pydantic import BaseModel, Field


class EligibilityResult(BaseModel):
    eligible: bool

    python_evidence: list[str] = Field(default_factory=list)
    ai_evidence: list[str] = Field(default_factory=list)

    rejection_reasons: list[str] = Field(default_factory=list)


class ScoreBreakdown(BaseModel):
    ai_project_depth: float = 0
    python_backend: float = 0
    cloud_fullstack: float = 0
    engineering_depth: float = 0
    github: float = 0

    total: float = 0


class GitHubResult(BaseModel):
    status: str = "not_checked"
    score: float = 0
    summary: str = ""


class ScreeningResult(BaseModel):
    rank: int | None = None
    candidate_name: str | None = None
    eligible: bool

    score: ScoreBreakdown | None = None

    matched_skills: list[str] = Field(default_factory=list)
    strengths: list[str] = Field(default_factory=list)
    concerns: list[str] = Field(default_factory=list)

    eligibility: EligibilityResult

    github: GitHubResult | None = None

    project_summary: str = ""
    github_summary: str = ""
    extraction_method: str = "pymupdf"


class BatchSummary(BaseModel):
    total_resumes: int
    successfully_parsed: int
    eligible: int
    rejected: int
    failed: int


class ScreeningRun(BaseModel):
    summary: BatchSummary
    candidates: list[ScreeningResult]