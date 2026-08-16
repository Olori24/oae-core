class EngineeringVerificationMetrics:
    """
    Collects engineering verification metrics.
    """

    def collect(
        self,
        tests_passed,
        tests_failed,
        files_changed,
    ):
        total = tests_passed + tests_failed

        if total == 0:
            success_rate = 0.0
        else:
            success_rate = tests_passed / total

        return {
            "tests_passed": tests_passed,
            "tests_failed": tests_failed,
            "files_changed": files_changed,
            "success_rate": success_rate,
        }
