"""
Repository detector registry.
"""

from .detectors import PythonDetector


class DetectorRegistry:
    """Loads repository technology detectors."""

    def load(self):

        return [
            PythonDetector(),
        ]
