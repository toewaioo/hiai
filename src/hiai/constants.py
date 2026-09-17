"""Application constants."""

APP_NAME = "HIAI"
APP_VERSION = "0.1.0"
DEFAULT_PROVIDER = "openrouter"
DEFAULT_MODEL = "openrouter/free"
DEFAULT_BASE_URL = "https://openrouter.ai/api/v1"
DEFAULT_TIMEOUT = 120
DEFAULT_MAX_ITERATIONS = 20
DEFAULT_MAX_READ_BYTES = 1_000_000
DEFAULT_MAX_WRITE_BYTES = 2_000_000
DEFAULT_RATE_LIMIT = 20  # max API requests per minute
MAX_LIST_FILES = 500
MAX_SEARCH_RESULTS = 50
MAX_FILE_READ_SIZE = 1_000_000

GROQ_BASE_URL = "https://api.groq.com/openai/v1"
GROQ_DEFAULT_MODEL = "llama-3.3-70b-versatile"

USER_AGENT = f"HIAI/{APP_VERSION}"

IGNORED_DIRS = {
    ".git",
    ".hg",
    ".svn",
    "__pycache__",
    "node_modules",
    ".venv",
    "venv",
    "env",
    ".env",
    ".tox",
    ".nox",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    "dist",
    "build",
    ".eggs",
    "*.egg-info",
    ".cache",
    ".parcel-cache",
    ".next",
    ".nuxt",
    "target",
    "bin",
    "obj",
}

SENSITIVE_PATTERNS = {
    ".env",
    ".env.*",
    "*.pem",
    "*.key",
    "id_rsa",
    "id_ed25519",
    "credentials.json",
    "secrets.json",
}

ANSI_COLORS = {
    "reset": "\033[0m",
    "bold": "\033[1m",
    "dim": "\033[2m",
    "red": "\033[31m",
    "green": "\033[32m",
    "yellow": "\033[33m",
    "blue": "\033[34m",
    "magenta": "\033[35m",
    "cyan": "\033[36m",
    "white": "\033[37m",
}

BANNER = r"""
╦ ╦╦╔═╗╦
╠═╣║╠═╝║
╩ ╩╩╩  ╩
"""
