from fastapi import Header, HTTPException, status
from backend.config import settings


async def verify_access_code(x_access_code: str = Header(default="")) -> str:
    if not settings.ACCESS_CODE:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Server is missing a configured access code.",
        )

    if not x_access_code or x_access_code != settings.ACCESS_CODE:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing access code.",
        )

    return x_access_code
