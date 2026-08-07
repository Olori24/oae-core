from oae.governance.rfc_generator import RFCGenerator


def test_rfc_generator(tmp_path):

    target = RFCGenerator().generate(
        tmp_path,
        1,
        "Meta Generator Engine",
    )

    assert target.exists()

    assert "RFC-001" in target.read_text()

    assert "Motivation" in target.read_text()

    assert "Architecture" in target.read_text()
