from pathlib import Path


class Verifier:

    def verify_file(self, filename):

        path = Path(filename)

        if not path.exists():
            return False, "File does not exist."

        if path.is_dir():
            return False, "Expected a file but found a directory."

        if path.stat().st_size == 0:
            return False, "File is empty."

        return True, "Verification successful."
