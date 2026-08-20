import logging
from pathlib import Path


class LoggingEngine:
    """
    Creates a standard logger for generated applications.
    """

    def create_logger(self, root, name="oae"):
        root = Path(root)

        log_dir = root / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)

        logfile = log_dir / "application.log"

        logger = logging.getLogger(name)

        logger.setLevel(logging.INFO)

        formatter = logging.Formatter(
            "%(asctime)s | %(levelname)s | %(message)s"
        )

        if not any(
            isinstance(handler, logging.FileHandler)
            and Path(handler.baseFilename) == logfile
            for handler in logger.handlers
        ):
            file_handler = logging.FileHandler(logfile)
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)

        if not any(isinstance(handler, logging.StreamHandler) for handler in logger.handlers):
            stream_handler = logging.StreamHandler()
            stream_handler.setFormatter(formatter)
            logger.addHandler(stream_handler)

        return logger
