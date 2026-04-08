from datetime import datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


class Severity(str, Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    UNKNOWN = "UNKNOWN"


class Vulnerability(BaseModel):
    model_config = ConfigDict(use_enum_values=True)

    id: str = Field(..., description="CVE or GHSA identifier")
    severity: Severity
    package: str
    installed_version: str
    fixed_version: Optional[str] = None
    description: str = ""
    layer: Optional[str] = None
    title: Optional[str] = None


class Secret(BaseModel):
    type: str = Field(..., description="Type of secret detected")
    file: str
    line: Optional[int] = None
    description: str = ""
    matched_value: Optional[str] = None


class MalwareFinding(BaseModel):
    model_config = ConfigDict(use_enum_values=True)

    rule: str = Field(..., description="YARA rule or ClamAV signature that matched")
    file: str
    signature: Optional[str] = None
    severity: Severity = Severity.CRITICAL
    category: str = "malware"


class Misconfiguration(BaseModel):
    model_config = ConfigDict(use_enum_values=True)

    code: str = Field(..., description="Dockle check code (e.g. DKR0001)")
    title: str
    severity: Severity = Severity.HIGH
    description: str = ""


class BaseImageCheck(BaseModel):
    image: str
    approved: bool
    suggestion: Optional[str] = None


class SeverityBreakdown(BaseModel):
    critical: int = 0
    high: int = 0
    medium: int = 0
    low: int = 0

    def total(self) -> int:
        return self.critical + self.high + self.medium + self.low

    def has_critical_or_high(self) -> bool:
        return self.critical > 0 or self.high > 0


class ScanDetails(BaseModel):
    vulnerabilities: list[Vulnerability] = Field(default_factory=list)
    malware: list[MalwareFinding] = Field(default_factory=list)
    secrets: list[Secret] = Field(default_factory=list)
    misconfigurations: list[Misconfiguration] = Field(default_factory=list)
    base_image: Optional[BaseImageCheck] = None
