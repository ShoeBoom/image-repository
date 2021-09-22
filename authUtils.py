from datetime import datetime, timedelta
from os import getenv
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from passlib.context import CryptContext
from pydantic import BaseModel

import database

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def authenticate_user(username: str, password: str):
    user = database.get_user(username)
    if user is None:
        return None
    if not pwd_context.verify(password, user.password_hash):
        return None
    return user


class Token(BaseModel):
    access_token: str
    token_type: str


def create_access_token(username, expires_delta: Optional[timedelta] = None):
    to_encode = {"sub": username}
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, getenv("SECRET_KEY"), algorithm=getenv("ALGORITHM"))
    return encoded_jwt


class User(BaseModel):
    username: str


class TokenData(BaseModel):
    username: Optional[str] = None


optional_oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token", auto_error=False)


async def optional_get_user_from_token(token: str = Depends(optional_oauth2_scheme)):
    if token is None:
        return None
    else:
        user = __get_user_from_token_helper(token)
        return user


async def get_user_from_token(token: str = Depends(oauth2_scheme)):
    user = __get_user_from_token_helper(token)
    return user


def __get_user_from_token_helper(token):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, getenv("SECRET_KEY"), algorithms=[getenv("ALGORITHM")])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception
    user = database.get_user(username=token_data.username)
    if user is None:
        raise credentials_exception
    return user
