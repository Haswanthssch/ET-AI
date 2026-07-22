from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse

from backend import models, dependencies
from backend.database import get_user, FAKE_USER_DB
from backend.security import (
    create_access_token,
    verify_password,
    ACCESS_TOKEN_EXPIRE_MINUTES,
)

router = APIRouter(
    prefix="/auth",
    tags=["authentication"],
)

def authenticate_user(username: str, password: str):
    user = get_user(FAKE_USER_DB, username)
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user

@router.post("/token")
async def login_for_access_token(form_data: models.LoginRequest):
    """
    Handles user login.
    1. If no role is provided, it returns the available roles for the user.
    2. If a valid role is provided, it returns a JWT access token.
    """
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # If no role is selected, return the list of available roles
    if not form_data.role:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "detail": "Role not selected. Please choose one of the following roles.",
                "available_roles": user.available_roles
            }
        )

    # If a role is selected, validate it
    if form_data.role not in user.available_roles:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid role selected. Please choose one of: {', '.join(user.available_roles)}",
        )

    # Create and return the access token with the selected role
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username, "role": form_data.role},
        expires_delta=access_token_expires,
    )

    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/users/me", response_model=models.User)
async def read_users_me(current_user: models.User = Depends(dependencies.get_current_user)):
    """
    A protected endpoint to get the current user's information.
    """
    return current_user


@router.get("/admin/dashboard", dependencies=[Depends(dependencies.RoleChecker(["admin"]))])
async def get_admin_dashboard():
    """An example endpoint only accessible by users with the 'admin' role."""
    return {"message": "Welcome to the Admin Dashboard!"}