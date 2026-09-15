from pydantic import BaseModel, Field


class Experience(BaseModel):
    company: str
    role: str
    description: str = ""
    technologies: list[str] = Field(default_factory=list)


class Project(BaseModel):
    name: str
    description: str = ""
    technologies: list[str] = Field(default_factory=list)
    evidence: list[str] = Field(default_factory=list)


class ResumeData(BaseModel):
    candidate_name: str | None = None
    email: str | None = None
    phone: str | None = None

    skills: list[str] = Field(default_factory=list)
    education: list[str] = Field(default_factory=list)
    experience: list[Experience] = Field(default_factory=list)
    projects: list[Project] = Field(default_factory=list)

    github_url: str | None = None

    # Keep original text for auditability/debugging.
    raw_text: str = ""