from pathlib import Path


class RFCGenerator:
    """
    Generates architecture RFC documents.
    """

    def generate(
        self,
        root,
        number: int,
        title: str,
    ):

        root = Path(root)

        architecture = (
            root
            / "docs"
            / "architecture"
        )

        architecture.mkdir(
            parents=True,
            exist_ok=True,
        )

        filename = (
            f"RFC-{number:03d}-"
            + title.lower().replace(" ", "-")
            + ".md"
        )

        target = architecture / filename

        target.write_text(
f"""# RFC-{number:03d}: {title}

Status
------
Draft

## Motivation

Describe why this capability exists.

## Goals

-

## Non-Goals

-

## Architecture

TBD

## Implementation

TBD

## Security

TBD

## Testing

TBD

## Acceptance Criteria

-
"""
        )

        return target
