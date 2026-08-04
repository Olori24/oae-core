from oae.repository.detector_registry import DetectorRegistry


def test_detector_registry():

    registry = DetectorRegistry()

    detectors = registry.load()

    assert len(detectors) >= 1
