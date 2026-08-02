from .tool import Tool

TOOLS = {
    "shell": Tool("shell", "Execute shell commands"),
    "git": Tool("git", "Git operations"),
    "python": Tool("python", "Execute Python code"),
    "filesystem": Tool("filesystem", "Read and write files"),
}
