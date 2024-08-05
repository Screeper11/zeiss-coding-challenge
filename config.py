import os


class Settings:
    # Database settings
    DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@db/arxivdb")

    # ArXiv API settings
    ARXIV_API_URL = "https://export.arxiv.org/api/query"
    MAX_RESULTS_PER_QUERY: int = 100

    # Backend API settings
    BACKEND_API_HOST = "0.0.0.0"
    BACKEND_API_PORT = 8000
    BACKEND_API_URL = f"http://api:{BACKEND_API_PORT}"

    # Frontend settings
    FRONTEND_HOST = "0.0.0.0"
    FRONTEND_PORT = 5001
    FRONTEND_API_URL = BACKEND_API_URL

    # CORS settings
    BACKEND_CORS_ORIGINS = [
        f"http://localhost:{FRONTEND_PORT}",
        f"http://127.0.0.1:{FRONTEND_PORT}",
    ]

    # Logging
    LOG_LEVEL = "INFO"


settings = Settings()
