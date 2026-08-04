from oae.core.kernel import Kernel


def test_kernel_lifecycle():

    kernel = Kernel()

    assert kernel.ready() is False

    kernel.initialize()

    assert kernel.ready() is True

    result = kernel.execute("Mission 059")

    assert result.mission == "Mission 059"

    report = kernel.health()

    assert report["kernel"] is True

    kernel.shutdown()

    assert kernel.ready() is False

