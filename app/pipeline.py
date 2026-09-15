from pathlib import Path

from app.enrichment.github import GitHubEnricher
from app.extraction.resume_assessor import ResumeAssessor
from app.extraction.resume_extractor import ResumeExtractor
from app.models.result import (
    BatchSummary,
    EligibilityResult,
    ScreeningResult,
    ScreeningRun,
)
from app.parsers.pdf import PDFExtractionError, extract_text_from_pdf
from app.screening.eligibility import check_eligibility
from app.screening.scorer import calculate_score


def discover_resumes(input_dir: str | Path) -> list[Path]:
    """
    Find all PDF resumes in the input directory.

    Deduplicate files by their resolved filesystem path.
    """
    directory = Path(input_dir)

    if not directory.exists():
        raise FileNotFoundError(
            f"Input directory not found: {directory}"
        )

    if not directory.is_dir():
        raise NotADirectoryError(
            f"Not a directory: {directory}"
        )

    files = {
        path.resolve()
        for path in directory.iterdir()
        if path.is_file()
        and path.suffix.lower() == ".pdf"
    }

    return sorted(files)


def process_resume(
    path: Path,
    extractor: ResumeExtractor,
    assessor: ResumeAssessor,
    github_enricher: GitHubEnricher,
) -> ScreeningResult:
    """
    Process one resume through the complete screening pipeline.
    """

    # 1. PDF → raw text
    text = extract_text_from_pdf(path)

    if not text.strip():
        raise PDFExtractionError(
            f"No text could be extracted from {path.name}"
        )

    # 2. Raw text → structured candidate data
    resume = extractor.extract(text)

    # 3. Hard eligibility filter
    eligibility = check_eligibility(resume)

    if not eligibility.eligible:
        return ScreeningResult(
            candidate_name=resume.candidate_name,
            eligible=False,
            score=None,
            matched_skills=resume.skills,
            strengths=[],
            concerns=eligibility.rejection_reasons,
            eligibility=eligibility,
            github=None,
            project_summary="",
            github_summary="",
            extraction_method="pymupdf",
        )

    # 4. Semantic project/engineering assessment
    assessment = assessor.assess(resume)

    # 5. GitHub enrichment
    github = github_enricher.enrich(resume.github_url)

    # 6. Final score is calculated by Python
    score = calculate_score(
        assessment,
        github_score=github.score,
    )

    return ScreeningResult(
        candidate_name=resume.candidate_name,
        eligible=True,
        score=score,
        matched_skills=resume.skills,
        strengths=assessment.strengths,
        concerns=assessment.concerns,
        eligibility=eligibility,
        github=github,
        project_summary=assessment.project_summary,
        github_summary=github.summary,
        extraction_method="pymupdf",
    )


def screen_resumes(
    input_dir: str | Path,
) -> ScreeningRun:
    """
    Process every PDF in the input directory.

    A failure for one resume does not terminate the batch.
    """

    resumes = discover_resumes(input_dir)

    extractor = ResumeExtractor()
    assessor = ResumeAssessor()
    github_enricher = GitHubEnricher()

    results: list[ScreeningResult] = []

    for resume_path in resumes:
        try:
            result = process_resume(
                resume_path,
                extractor,
                assessor,
                github_enricher,
            )

            # IMPORTANT: keep successfully processed results.
            results.append(result)

        except Exception as exc:
            failed_eligibility = EligibilityResult(
                eligible=False,
                rejection_reasons=[
                    f"Processing failed: {exc}"
                ],
            )

            result = ScreeningResult(
                candidate_name=resume_path.stem,
                eligible=False,
                score=None,
                matched_skills=[],
                strengths=[],
                concerns=[
                    f"Processing failed: {exc}"
                ],
                eligibility=failed_eligibility,
                github=None,
                project_summary="",
                github_summary="",
                extraction_method="pymupdf",
            )

            results.append(result)

    # Rank eligible candidates only.
    eligible_candidates = [
        result
        for result in results
        if result.eligible and result.score is not None
    ]

    eligible_candidates.sort(
        key=lambda result: result.score.total,
        reverse=True,
    )

    for rank, result in enumerate(
        eligible_candidates,
        start=1,
    ):
        result.rank = rank

    failed_count = sum(
        1
        for result in results
        if any(
            reason.startswith("Processing failed:")
            for reason in result.eligibility.rejection_reasons
        )
    )

    rejected_count = sum(
        1
        for result in results
        if not result.eligible
        and not any(
            reason.startswith("Processing failed:")
            for reason in result.eligibility.rejection_reasons
        )
    )

    summary = BatchSummary(
        total_resumes=len(results),
        successfully_parsed=len(results) - failed_count,
        eligible=len(eligible_candidates),
        rejected=rejected_count,
        failed=failed_count,
    )

    return ScreeningRun(
        summary=summary,
        candidates=results,
    )