import os
import secrets

# Load .env if present (very small loader, no extra dependency)
_env_path = os.path.join(os.path.dirname(__file__), "..", ".env")

if os.path.exists(_env_path):
    with open(_env_path) as env_file:
        for line in env_file:
            line = line.strip()

            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip())


APP_ENV = os.getenv("APP_ENV", "development")

SECRET_KEY = os.getenv("SECRET_KEY")

if APP_ENV == "production":
    if not SECRET_KEY:
        raise RuntimeError(
            "SECRET_KEY must be set in production"
        )

    if len(SECRET_KEY) < 32:
        raise RuntimeError(
            "SECRET_KEY must be at least 32 characters in production"
        )
else:
    # Safe local/test fallback: random per process.
    # Never use a predictable hard-coded secret.
    SECRET_KEY = SECRET_KEY or secrets.token_urlsafe(32)


DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "sqlite:///./aipulse.db",
)

AI_MODE = os.getenv(
    "AI_MODE",
    "mock",
)  # "mock" or "live"

LLM_API_URL = os.getenv(
    "LLM_API_URL",
    "",
)

LLM_API_KEY = os.getenv(
    "LLM_API_KEY",
    "",
)

LLM_MODEL = os.getenv(
    "LLM_MODEL",
    "",
)

TOKEN_HOURS = 12