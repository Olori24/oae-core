from oae.core.kernel import Kernel


def test_dependency_validation():

    kernel = Kernel()

    kernel.validate_dependencies()

    assert True
