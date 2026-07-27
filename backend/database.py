from typing import Dict, Optional
from backend.models import UserInDB

# In-memory "database" for users
# In a real application, this would be a connection to a real database (e.g., PostgreSQL, MySQL)
#
# Demo credentials (all use password: etai123)
#   admin@etai.com  -> all persona dashboards + admin
#   exec@etai.com   -> executive
#   procure@etai.com-> procurement
#   engineer@etai.com-> engineer
#   qa@etai.com     -> qa_qc
#
# The four persona roles map 1:1 to the frontend dashboards:
#   executive | procurement | engineer | qa_qc

# bcrypt hash of "etai123"
_ETAI123 = "$2b$12$PYS6j/cvYILxvaT5DCBgXuXiQq8vN05S1ehCzf9yC3sjM6z4dtv.6"

FAKE_USER_DB: Dict[str, Dict] = {
    "admin@etai.com": {
        "username": "admin@etai.com",
        "full_name": "Platform Admin",
        "email": "admin@etai.com",
        "hashed_password": _ETAI123,
        "disabled": False,
        "available_roles": ["executive", "procurement", "engineer", "qa_qc", "admin"],
    },
    "exec@etai.com": {
        "username": "exec@etai.com",
        "full_name": "Executive User",
        "email": "exec@etai.com",
        "hashed_password": _ETAI123,
        "disabled": False,
        "available_roles": ["executive"],
    },
    "procure@etai.com": {
        "username": "procure@etai.com",
        "full_name": "Procurement Lead",
        "email": "procure@etai.com",
        "hashed_password": _ETAI123,
        "disabled": False,
        "available_roles": ["procurement"],
    },
    "engineer@etai.com": {
        "username": "engineer@etai.com",
        "full_name": "Site Engineer",
        "email": "engineer@etai.com",
        "hashed_password": _ETAI123,
        "disabled": False,
        "available_roles": ["engineer"],
    },
    "qa@etai.com": {
        "username": "qa@etai.com",
        "full_name": "QA/QC Engineer",
        "email": "qa@etai.com",
        "hashed_password": _ETAI123,
        "disabled": False,
        "available_roles": ["qa_qc"],
    },
}

def get_user(db: Dict, username: str) -> Optional[UserInDB]:
    """Retrieve a user from the database."""
    if username in db:
        user_dict = db[username]
        return UserInDB(**user_dict)
    return None