"""FastAPI dependency injection helpers."""

from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import TokenData, decode_token
from app.db.models import UserRole
from app.db.session import get_db

security = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(security)],
) -> TokenData:
    """Extract and validate the JWT token from the Authorization header."""
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    try:
        return decode_token(credentials.credentials)
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def require_analyst(
    current_user: Annotated[TokenData, Depends(get_current_user)],
) -> TokenData:
    """Require the analyst role."""
    if current_user.role != UserRole.ANALYST:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Analyst role required",
        )
    return current_user


# Type aliases for cleaner route signatures
CurrentUser = Annotated[TokenData, Depends(get_current_user)]
AnalystUser = Annotated[TokenData, Depends(require_analyst)]
DBSession = Annotated[AsyncSession, Depends(get_db)]
