from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from passlib.context import CryptContext
from datetime import datetime, timedelta
from jose import JWTError, jwt
from sqlmodel import Session, select

from app.core.config import settings
from app.schemas.auth import UserSignInschema, UserLoginSchema

from app.models.user import User


bycrypt_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth_bearer = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token")


def create_access_token(data: dict, expires_delta: int | None = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + timedelta(minutes=expires_delta)
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        to_encode, settings.secret_key, algorithm=settings.algorithm
    )
    return encoded_jwt


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bycrypt_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return bycrypt_context.hash(password)


def get_current_user(token: str = Depends(oauth_bearer)) -> dict:
    try:
        payload = jwt.decode(
            token, settings.secret_key, algorithms=[settings.algorithm]
        )
        subject: str = payload.get("sub")
        email: str | None = payload.get("email")

        if subject is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
            )
        return {"phone_number": subject, "email": email}
    except JWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
        ) from exc


async def sign_in_user(user: "UserSignInschema", db: Session) -> str:
    # check if phone or email already exists
    existing_user = (
        db.query(User)
        .filter((User.phone_number == user.phone_number) | (User.email == user.email))
        .first()
    )
    if existing_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User already exists")

    # Hash the password
    hashed_password = get_password_hash(user.password)

    # Create a new user instance
    new_user = User(username=user.phone_number, email=user.email, phone_number=user.phone_number, hashed_password=hashed_password)

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    access_token_expires = settings.access_token_expire_minutes
    access_token = create_access_token(
        data={"sub": new_user.phone_number, "email": new_user.email},
        expires_delta=access_token_expires,
    )

    return access_token


async def login_user(users: "UserLoginSchema", db: Session) -> str:
    # try to find by phone_number first, then email
    query = db.query(User)
    if users.phone_number:
        user = query.filter(User.phone_number == users.phone_number).first()
    else:
        user = query.filter(User.email == users.email).first()

    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    if not verify_password(users.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    access_token_expires = settings.access_token_expire_minutes
    access_token = create_access_token(
        data={"sub": user.phone_number, "email": user.email},
        expires_delta=access_token_expires,
    )
    return access_token


async def login_with_access_token(
    db: Session, form_data: OAuth2PasswordRequestForm = Depends()
) -> str:
    try:

        identifier: str = form_data.username
        password: str = form_data.password

        if identifier is None or password is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

        # decide whether identifier is phone or email
        if "@" in identifier:
            login_schema = UserLoginSchema(email=identifier, password=password)
        else:
            login_schema = UserLoginSchema(phone_number=identifier, password=password)

        token = await login_user(login_schema, db)
        return {"access_token": token, "token_type": "bearer"}
    except JWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
        ) from exc





async def get_user_by_email(db: Session, email: str):
    return db.exec(select(User).where(User.email == email)).first()


async def get_user_by_phone(db: Session, phone: str):
    return db.exec(select(User).where(User.phone_number == phone)).first()









