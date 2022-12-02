from datetime import datetime

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from pydantic import ValidationError

from apps.authentication.domain import TokenPayload
from apps.users.domain import User
from apps.users.services import UsersCRUD
from config import settings

oauth2_oauth = OAuth2PasswordBearer(
    tokenUrl="/refresh-access-token", scheme_name="Bearer"
)


async def get_current_user(token: str = Depends(oauth2_oauth)) -> User:
    try:
        payload = jwt.decode(
            token,
            settings.authentication.secret_key,
            algorithms=[settings.authentication.algorithm],
        )
        token_data = TokenPayload(**payload)

        if datetime.fromtimestamp(token_data.exp) < datetime.now():
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token expired",
                headers={"WWW-Authenticate": "Bearer"},
            )
    except (JWTError, ValidationError):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user: User = await UsersCRUD().get_by_email(email=token_data.sub)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Could not find user",
        )

    return user