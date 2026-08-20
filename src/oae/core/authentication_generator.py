from pathlib import Path


class AuthenticationGenerator:
    """Generate authentication scaffolding without shipping secret literals."""

    def generate(self, root):
        root = Path(root)
        auth = root / "src" / "auth"
        auth.mkdir(parents=True, exist_ok=True)
        models = root / "src" / "models"
        models.mkdir(parents=True, exist_ok=True)
        api = root / "src" / "api"
        api.mkdir(parents=True, exist_ok=True)

        (auth / "__init__.py").write_text("", encoding="utf-8")
        (auth / "security.py").write_text(
            '''import os

SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY:
    raise ValueError("SECRET_KEY must be set in the environment.")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
''',
            encoding="utf-8",
        )
        (auth / "password.py").write_text(
            '''import hashlib


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()
''',
            encoding="utf-8",
        )
        (auth / "jwt.py").write_text(
            '''def create_access_token(data):
    return {"access_token": data}
''',
            encoding="utf-8",
        )
        (models / "__init__.py").write_text("", encoding="utf-8")
        (models / "user.py").write_text(
            '''from sqlalchemy import Column, Integer, String
from src.database.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(255), unique=True)
    email = Column(String(255), unique=True)
    password = Column(String(255))
''',
            encoding="utf-8",
        )
        (api / "auth.py").write_text(
            '''from fastapi import APIRouter

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register")
def register():
    return {"message": "User Registered"}


@router.post("/login")
def login():
    return {"message": "Login Successful"}
''',
            encoding="utf-8",
        )
        return auth
