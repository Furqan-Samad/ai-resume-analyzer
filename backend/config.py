import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    GEMINI_API_KEY: str = os.environ.get("GEMINI_API_KEY", "")
    ACCESS_CODE: str = os.environ.get("ACCESS_CODE", "")
    GEMINI_MODEL: str = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")
    ALLOWED_ORIGINS: list = [
        origin.strip()
        for origin in os.environ.get("ALLOWED_ORIGINS", "*").split(",")
        if origin.strip()
    ]
    RATE_LIMIT: str = os.environ.get("RATE_LIMIT", "10/hour")
    MAX_PDF_SIZE_MB: int = int(os.environ.get("MAX_PDF_SIZE_MB", "10"))


settings = Settings()
