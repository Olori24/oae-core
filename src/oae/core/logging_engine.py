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

        if not logger.handlers:
            formatter = logging.Formatter(
                "%(asctime)s | %(levelname)s | %(message)s"
            )

            file_handler = logging.FileHandler(logfile)
            file_handler.setFormatter(formatter)

            stream_handler = logging.StreamHandler()
            stream_handler.setFormatter(formatter)

            logger.addHandler(file_handler)
            logger.addHandler(stream_handler)

        return logger
