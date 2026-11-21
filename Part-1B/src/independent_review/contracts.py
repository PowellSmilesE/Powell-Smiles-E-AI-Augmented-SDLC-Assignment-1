"""Stable external contract used by both application and independent checks."""

from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class Category(str, Enum):
    SQL_INJECTION = "sql_injection"
    COMMAND_INJECTION = "command_injection"
    XSS = "cross_site_scripting"
    PATH_TRAVERSAL = "path_traversal"
    DESERIALIZATION = "unsafe_deserialization"
    HARDCODED_SECRET = "hardcoded_secret"  # nosec B105
    WEAK_CRYPTO = "weak_cryptography"
    TLS = "tls_verification_disabled"
    AUTHORIZATION = "broken_authorization"
    TEMPFILE = "insecure_tempfile"


class Severity(str, Enum):
    CRITICAL = "Critical"
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"


class Finding(BaseModel):
    model_config = ConfigDict(extra="forbid")
    category: Category
    severity: Severity
    start_line: int = Field(ge=1)
    end_line: int = Field(ge=1)
    evidence: str = Field(min_length=1, max_length=300)
    explanation: str = Field(min_length=25, max_length=1800)
    remediation: str = Field(min_length=25, max_length=1800)


class ReviewResult(BaseModel):
    model_config = ConfigDict(extra="forbid")
    analysis_summary: str = Field(min_length=5, max_length=600)
    findings: list[Finding] = Field(max_length=30)


class ReviewRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    source: str = Field(min_length=1, max_length=25000)
    consent_external_transfer: bool


class ReviewEnvelope(BaseModel):
    review_required: bool = True
    model_output: ReviewResult
