class FailureClassifier:
    """
    Classifies repository execution failures into
    deterministic engineering categories.
    """

    def classify(self, result):
        """
        Classify a test/execution result.
        """

        if not result:
            return "UNKNOWN_FAILURE"

        if result.get("passed") is True:
            return "NO_FAILURE"

        stderr = (result.get("stderr") or "").lower()
        stdout = (result.get("stdout") or "").lower()

        output = f"{stderr}\n{stdout}"

        if "importerror" in output or "modulenotfounderror" in output:
            return "IMPORT_ERROR"

        if "syntaxerror" in output:
            return "SYNTAX_ERROR"

        if "assertionerror" in output:
            return "TEST_FAILURE"

        if "traceback" in output:
            return "RUNTIME_ERROR"

        if result.get("returncode") not in (None, 0):
            return "COMMAND_ERROR"

        return "UNKNOWN_FAILURE"
