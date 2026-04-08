from datetime import datetime, timezone
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict

from src.models.findings import (
    SeverityBreakdown,
    ScanDetails,
    Vulnerability,
    Secret,
    MalwareFinding,
    Misconfiguration,
    BaseImageCheck,
)


class ScanStatus(str, Enum):
    PASS = "PASS"
    WARN = "WARN"
    BLOCKED = "BLOCKED"


class Verdict(str, Enum):
    POLICY_PASSED = "policy_passed"
    POLICY_VIOLATION = "policy_violation"
    ADVISORY_WARNING = "advisory_warning"


class Warning(BaseModel):
    type: str
    count: int
    message: str


class ScanResponse(BaseModel):
    model_config = ConfigDict(use_enum_values=True)

    status: ScanStatus
    verdict: Verdict
    image_tag: str
    scan_duration_seconds: float
    severity_breakdown: SeverityBreakdown
    block_reason: Optional[str] = None
    policy_passed: bool
    signed: bool = False
    signature: Optional[str] = None
    warnings: list[Warning] = Field(default_factory=list)
    details: ScanDetails = Field(default_factory=ScanDetails)


class ToolStatus(BaseModel):
    trivy: str = "unknown"
    clamav: str = "unknown"
    yara: str = "unknown"
    trufflehog: str = "unknown"
    dockle: str = "unknown"
    cosign: str = "unknown"


class HealthResponse(BaseModel):
    status: str = "healthy"
    service: str = "security-scanner"
    tools: ToolStatus = Field(default_factory=ToolStatus)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
