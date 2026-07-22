from typing import Dict, Optional
from backend.models import UserInDB

# In-memory "database" for users
# In a real application, this would be a connection to a real database (e.g., PostgreSQL, MySQL)
# The password for 'admin' is 'adminpass', for 'dev' is 'devpass'
FAKE_USER_DB: Dict[str, Dict] = {
    "admin@example.com": {
        "username": "admin@example.com",
        "full_name": "Admin User",
        "email": "admin@example.com",
        "hashed_password": "$2b$12$EixZaBfW3G9yS9hTjC0X/u3jZpLd3bJ5/IZmC.9y2T2/fBE5zJg/q",
        "disabled": False,
        "available_roles": ["admin", "developer", "viewer"],
    },
    "dev@example.com": {
        "username": "dev@example.com",
        "full_name": "Dev User",
        "email": "dev@example.com",
        "hashed_password": "$2b$12$zT.xN.cWJ2yVfLSAbpLwUuFw0i/g/aR4b.9aB.xG3f2aH4zS5f3e.",
        "disabled": False,
        "available_roles": ["developer", "viewer"],
    },
}

def get_user(db: Dict, username: str) -> Optional[UserInDB]:
    """Retrieve a user from the database."""
    if username in db:
        user_dict = db[username]
        return UserInDB(**user_dict)
    return None