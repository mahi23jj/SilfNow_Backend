from typing import Optional

from pydantic import BaseModel, Field, EmailStr, ValidationError, model_validator


class UserSignInschema(BaseModel):
    phone_number: str = Field(..., description="User phone number")
    email: Optional[EmailStr] = Field(None, description="Optional email address")
    password: str = Field(..., min_length=8, description="Password must be at least 8 characters long")
    password_confirm: str = Field(..., description="Confirm your password")

    @model_validator(mode="after")
    def passwords_match(self) -> "UserSignInschema":
        if self.password != self.password_confirm:
            raise ValidationError([{"loc": ("password_confirm",), "msg": "Passwords do not match", "type": "value_error"}], self.__class__)
        return self


class UserSignInResponseSchema(BaseModel):
    access_token: str
    token_type: str = "bearer"

    class Config:
        schema_extra = {
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "bearer",
            }
        }


class UserLoginSchema(BaseModel):
    phone_number: Optional[str] = Field(default=None, description="Phone number of the user")
    email: Optional[EmailStr] = Field(default=None, description="Email of the user")
    password: str = Field(..., min_length=8, description="Password must be at least 8 characters long")

    @model_validator(mode="after")
    def phone_or_email(self) -> "UserLoginSchema":
        if not self.phone_number and not self.email:
            raise ValueError("Either phone_number or email must be provided")
        return self
