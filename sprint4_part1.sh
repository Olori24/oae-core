#!/data/data/com.termux/files/usr/bin/bash

mkdir -p src/oae/git

touch src/oae/git/__init__.py

cat > src/oae/git/branch.py <<'PY'
import subprocess

class GitBranch:

    def current(self):
        try:
            return subprocess.check_output(
                ["git", "branch", "--show-current"],
                text=True,
            ).strip()
        except Exception:
            return "unknown"
PY

cat > src/oae/git/status.py <<'PY'
import subprocess

class GitStatus:

    def status(self):
        try:
            output = subprocess.check_output(
                ["git", "status", "--short"],
                text=True,
            ).strip()

            if not output:
                return {"clean": True, "files": []}

            return {
                "clean": False,
                "files": output.splitlines(),
            }

        except Exception as e:
            return {
                "clean": False,
                "error": str(e),
            }
PY

cat > src/oae/git/history.py <<'PY'
import subprocess

class GitHistory:

    def recent(self, limit=5):
        try:
            output = subprocess.check_output(
                [
                    "git",
                    "log",
                    f"-{limit}",
                    "--pretty=format:%h | %an | %s",
                ],
                text=True,
            )

            return output.splitlines()

        except Exception as e:
            return [str(e)]
PY

cat > src/oae/git/diff.py <<'PY'
import subprocess

class GitDiff:

    def summary(self):
        try:
            output = subprocess.check_output(
                ["git", "diff", "--stat"],
                text=True,
            ).strip()

            return output if output else "No unstaged changes."

        except Exception as e:
            return str(e)
PY

echo ""
echo "=================================="
echo " Sprint 4 Part 1 Installed"
echo "=================================="
echo ""
EOFchmod +x sprint4_part1.sh
./sprint4_part1.sh

