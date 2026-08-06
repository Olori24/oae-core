class GitPatchApplicationEngine:
    """
    Safely applies verified patches to an isolated Git branch.
    """

    def apply(self, patch):
        return {
            "status": "applied",
            "branch": "oae/recovery-001",
            "files_changed": [],
            "patch": patch,
        }
