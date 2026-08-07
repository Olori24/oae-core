class RepositoryOperationMapper:
    """
    Converts engineering operations into
    repository execution requests.
    """

    def map(self, operation):

        mapping = {
            "create_file": "repository_create_file",
            "modify_file": "repository_modify_file",
            "run_tests": "repository_run_tests",
            "commit_changes": "repository_commit",
        }

        return mapping.get(
            operation,
            "unknown_operation",
        )
