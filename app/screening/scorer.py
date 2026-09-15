from app.models.assessment import CandidateAssessment
from app.models.result import ScoreBreakdown


def calculate_score(
    assessment: CandidateAssessment,
    github_score: float = 0,
) -> ScoreBreakdown:
    """
    Convert semantic assessment + GitHub enrichment into the final score.

    The LLM supplies bounded category scores.
    Python owns the final arithmetic and bounds.
    """

    github_score = max(0.0, min(github_score, 10.0))

    total = (
        assessment.ai_project_depth
        + assessment.python_backend_depth
        + assessment.cloud_fullstack_depth
        + assessment.engineering_depth
        + github_score
        - assessment.shallow_project_penalty
    )

    total = max(0.0, min(total, 100.0))

    return ScoreBreakdown(
        ai_project_depth=assessment.ai_project_depth,
        python_backend=assessment.python_backend_depth,
        cloud_fullstack=assessment.cloud_fullstack_depth,
        engineering_depth=assessment.engineering_depth,
        github=github_score,
        total=round(total, 2),
    )