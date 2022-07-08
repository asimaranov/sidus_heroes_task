from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from starlette import status
from passlib.context import CryptContext

from database import database, users
from jose import JWTError, jwt

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

SECRET_KEY = "5ad00c5983e369c5003797c0bd9d3a610c92c22330d0f0e2e7abb7d1d47bb405"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 30


async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: int = payload.get("sub")
        if not username:
            raise credentials_exception

    except JWTError:
        raise credentials_exception
    user_info = await database.fetch_one(users.select().where(users.c.username == username))
    if not user_info:
        raise credentials_exception

    if user_info.is_banned:
        raise HTTPException(status_code=400, detail="User is banned")

    return user_info

