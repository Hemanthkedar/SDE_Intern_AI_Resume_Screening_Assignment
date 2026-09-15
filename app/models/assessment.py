from pydantic import BaseModel, Field


class CandidateAssessment(BaseModel):
    ai_project_depth: float = Field(ge=0, le=40)

    python_backend_depth: float = Field(ge=0, le=30)

    cloud_fullstack_depth: float = Field(ge=0, le=15)

    engineering_depth: float = Field(ge=0, le=5)

    shallow_ai_project: bool = False

    shallow_project_penalty: float = Field(
        default=0,
        ge=0,
        le=15,
    )

    project_summary: str = ""

    strengths: list[str] = Field(default_factory=list)

    concerns: list[str] = Field(default_factory=list)

    evidence: list[str] = Field(default_factory=list)