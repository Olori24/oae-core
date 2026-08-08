class ExecutionOutcomeAnalyzer:
    """
    Analyzes mission execution records and produces engineering outcome metrics.
    """

    def analyze(self, records):
        total = len(records)

        completed = sum(
            1
            for record in records
            if record.get("status") == "completed"
            or (
                "status" not in record
                and record.get("success") is True
            )
        )

        failed = sum(
            1
            for record in records
            if record.get("status") == "failed"
            or (
                "status" not in record
                and record.get("success") is False
            )
        )

        recovery_required = sum(
            1
            for record in records
            if record.get("status") == "recovery_required"
        )

        success_rate = (
            completed / total
            if total
            else 0
        )

        return {
            "total": total,
            "completed": completed,
            "failed": failed,
            "recovery_required": recovery_required,
            "success_rate": success_rate,
        }
