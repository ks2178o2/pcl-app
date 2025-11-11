import os
from pathlib import Path
from typing import Iterable

from dotenv import load_dotenv


def load_test_env(extra_candidates: Iterable[str] | None = None) -> None:
    """
    Attempt to load environment variables for tests without failing on
    sandbox permission errors. Prefers DOTENV_PATH and an optional list
    of extra candidate files.
    """
    candidates: list[Path] = []

    override = os.getenv("DOTENV_PATH")
    if override:
        candidates.append(Path(override).expanduser())

    if extra_candidates:
        candidates.extend(Path(p).expanduser() for p in extra_candidates)

    for env_path in candidates:
        try:
            if env_path.exists():
                load_dotenv(env_path)
                break
        except (PermissionError, OSError):
            # Skip files the sandbox cannot read
            continue

