from pathlib import Path


class AuthenticationGenerator:
    """
    Generates authentication scaffolding.
    """

    def generate(self, root):
        root = Path(root)

        auth = root / "src" / "auth"
        auth.mkdir(parents=True, exist_ok=True)

        models = root / "src" / "models"
        models.mkdir(parents=True, exist_ok=True)

        api = root / "src" / "api"
        api.mkdir(parents=True, exist_ok=True)

        (auth / "__init__.py").write_text("")

        (auth / "security.py").write_text(
"""SECRET_KEY = 'change-me'

ALGORITHM = 'HS256'

ACCESS_TOKEN_EXPIRE_MINUTES = 30
"""
        )

        (auth / "password.py").write_text(
"""import hashlib


def hash_password(password: str):
    return hashlib.sha256(
        password.encode()
    ).hexdigest()
"""
        )

        (auth / "jwt.py").write_text(
"""def create_access_token(data):
    return {"access_token": data}
"""
        )

        (models / "__init__.py").write_text("")

        (models / "user.py").write_text(
"""from sqlalchemy import Column, Integer, String
from src.database.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(255), unique=True)
    email = Column(String(255), unique=True)
    password = Column(String(255))
"""
        )

        (api / "auth.py").write_text(
"""from fastapi import APIRouter

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)


@router.post("/register")
def register():
    return {"message": "User Registered"}


@router.post("/login")
def login():
    return {"message": "Login Successful"}
"""
        )

        return auth
