from sqlalchemy.orm import Session

from auth.hashing import hash_password, verify_password
from auth.jwt_handler import create_access_token

from models.user import User
from schemas.auth import UserRegister, UserLogin


def register_user(db: Session, user: UserRegister):

    existing_user = (
        db.query(User)
        .filter(User.email == user.email)
        .first()
    )

    if existing_user:
        return None

    db_user = User(
        name=user.name,
        email=user.email,
        phone=user.phone,
        password_hash=hash_password(user.password),
        role="CITIZEN",
        is_verified=False,
        status="ACTIVE"
    )

    db.add(db_user)

    db.commit()

    db.refresh(db_user)

    return db_user


def login_user(db: Session, credentials: UserLogin):

    user = (
        db.query(User)
        .filter(User.email == credentials.email)
        .first()
    )

    if not user:
        return None

    if not verify_password(
        credentials.password,
        user.password_hash
    ):
        return None

    token = create_access_token(
        {
            "sub": user.email,
            "role": user.role,
            "user_id": user.id
        }
    )

    return {
        "access_token": token,
        "token_type": "bearer"
    }