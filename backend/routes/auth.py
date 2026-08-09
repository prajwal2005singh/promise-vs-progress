from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from database.db import get_db

from auth.dependencies import get_current_user

from models.user import User

from schemas.auth import (
    UserRegister,
    UserLogin,
    Token,
    CurrentUserResponse
)

from services.auth_service import (
    register_user,
    login_user
)

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"]
)


@router.post("/register")
def register(
    user: UserRegister,
    db: Session = Depends(get_db)
):

    db_user = register_user(db, user)

    if db_user is None:
        raise HTTPException(
            status_code=400,
            detail="Email already registered"
        )

    return {
        "message": "User registered successfully"
    }


@router.post(
    "/login",
    response_model=Token
)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):

    credentials = UserLogin(
        email=form_data.username,
        password=form_data.password
    )

    token = login_user(
        db,
        credentials
    )

    if token is None:
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password"
        )

    return token


@router.get(
    "/me",
    response_model=CurrentUserResponse
)
def read_current_user(
    current_user: User = Depends(get_current_user)
):
    """
    Lets the frontend restore who's logged in (and their role, to decide
    whether to show admin views) after a page refresh, using just the
    token stored client-side -- without this the SPA would have no way
    to recover session state without asking the person to log in again.
    """

    return current_user