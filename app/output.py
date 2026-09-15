import json
from pathlib import Path

from app.models.result import ScreeningRun


def write_results(
    result: ScreeningRun,
    output_path: str | Path,
) -> None:
    path = Path(output_path)

    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    path.write_text(
        json.dumps(
            result.model_dump(),
            indent=2,
        ),
        encoding="utf-8",
    )