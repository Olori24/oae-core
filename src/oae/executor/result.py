from dataclasses import dataclass


@dataclass
class ExecutionResult:
    success: bool
    output: str
