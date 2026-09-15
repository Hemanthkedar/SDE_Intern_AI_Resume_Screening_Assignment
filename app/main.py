import argparse

from dotenv import load_dotenv

from app.output import write_results
from app.pipeline import screen_resumes


load_dotenv()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="AI Resume Screening and Ranking System"
    )

    parser.add_argument(
        "--input",
        required=True,
        help="Directory containing resume PDFs",
    )

    parser.add_argument(
        "--output",
        required=True,
        help="Path for the generated JSON results",
    )

    args = parser.parse_args()

    result = screen_resumes(args.input)
    write_results(result, args.output)

    print(
        f"Processed: {result.summary.total_resumes} | "
        f"Eligible: {result.summary.eligible} | "
        f"Rejected: {result.summary.rejected} | "
        f"Failed: {result.summary.failed}"
    )


if __name__ == "__main__":
    main()