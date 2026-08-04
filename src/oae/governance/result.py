"""
Governance validation result.
"""

from dataclasses import dataclass, field


@dataclass
class ValidationResult:
    """Represents the outcome of governance validation."""

    approved: bool
    violations: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
