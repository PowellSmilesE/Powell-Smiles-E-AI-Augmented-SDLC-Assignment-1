"""Pure app logic. Never runs or writes supplied source."""

from .contracts import ReviewResult
from .prompt import SYSTEM_PROMPT, make_user_prompt
from .provider import GroqProvider


class InvalidReview(Exception):
    pass


def validate_evidence(result: ReviewResult, source: str) -> None:
    lines = source.splitlines()
    for finding in result.findings:
        if finding.end_line < finding.start_line or finding.end_line > len(lines):
            raise InvalidReview("Invalid source range")
        span = "\n".join(lines[finding.start_line - 1 : finding.end_line])
        if finding.evidence.strip() not in span:
            raise InvalidReview("Finding evidence does not occur in cited lines")


def review_source(source: str, provider: GroqProvider | None = None) -> ReviewResult:
    if not source.strip() or len(source) > 25000:
        raise InvalidReview("Invalid source size")
    raw = (provider or GroqProvider()).generate(SYSTEM_PROMPT, make_user_prompt(source))
    try:
        result = ReviewResult.model_validate(raw)
        validate_evidence(result, source)
    except Exception:
        # Suppress Pydantic details because provider output might contain secrets.
        raise InvalidReview("Model output failed schema or evidence validation") from None
    return result
