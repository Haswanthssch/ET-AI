from pydantic import BaseModel, EmailStr
from typing import List, Optional

class User(BaseModel):
    username: EmailStr
    full_name: Optional[str] = None
    disabled: Optional[bool] = None
    roles: List[str] = []

class UserInDB(User):
    hashed_password: str
    available_roles: List[str]

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None
    role: Optional[str] = None

class LoginRequest(BaseModel):
    username: str
    password: str
    role: Optional[str] = None # Role can be selected on login

class RoleSelection(BaseModel):
    username: str
    available_roles: List[str]