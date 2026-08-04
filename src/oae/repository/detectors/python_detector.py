"""
Python technology detector.
"""


class PythonDetector:

    def detect(self, root, profile):

        if (root / "pyproject.toml").exists():

            profile.language = "Python"
            profile.package_manager = "pip"

        return profile
