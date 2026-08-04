from oae.core.kernel import Kernel


def test_kernel_lifecycle():

    kernel = Kernel()

    assert kernel.ready() is False

    kernel.initialize()

    assert kernel.ready() is True

    report = kernel.health()

    assert report["kernel"] is True
    assert report["healthy_subsystems"] == 1
    assert report["total_subsystems"] == 1

    kernel.shutdown()

    assert kernel.ready() is False
