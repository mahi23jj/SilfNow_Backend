from typing import Optional

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    ValidationInfo,
    field_validator,
    model_validator,
    EmailStr,
)


class UserSignInschema(BaseModel):
    username: str
    email: EmailStr = Field(
        ..., pattern=r"^[\w\.-]+@[\w\.-]+\.\w+$", description="A valid email address"
    )
    password: str = Field(
        ..., min_length=8, description="Password must be at least 8 characters long"
    )
    password_confirm: str = Field(..., description="Confirm your password")

    @field_validator("password_confirm")
    @classmethod
    def passwords_match(cls, value: str, info: ValidationInfo) -> str:
        if info.data.get("password") != value:
            raise ValueError("Passwords do not match")
        return value


class UserSignInResponseSchema(BaseModel):
    access_token: str
    token_type: str = "bearer"

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "bearer",
            }
        }
    )


class GoogleAuthSchema(BaseModel):
    token: str = Field(..., min_length=10, description="Google ID token")


class UserLoginSchema(BaseModel):
    username: Optional[str] = Field(default=None, description="Username of the user")
    email: Optional[EmailStr] = Field(
        None, pattern=r"^[\w\.-]+@[\w\.-]+\.\w+$", description="A valid email address"
    )
    password: str = Field(
        ..., min_length=8, description="Password must be at least 8 characters long"
    )



    @model_validator(mode="after")
    def email_or_username(self) -> "UserLoginSchema":
        if not self.email and not self.username:
            raise ValueError("Either email or username must be provided")
        return self

