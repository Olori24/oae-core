from oae.core.logging_engine import LoggingEngine


def test_logger_creation(tmp_path):
    engine = LoggingEngine()

    logger = engine.create_logger(tmp_path)

    logger.info("OAE Test Log")

    assert (tmp_path / "logs").exists()
    assert (tmp_path / "logs" / "application.log").exists()
