from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, StringConstraints

from app.core.roles import home_path_for_role


class LoginRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    email: Annotated[
        str,
        StringConstraints(
            min_length=5,
            max_length=254,
            pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$",
        ),
    ]
    password: str = Field(min_length=8, max_length=128)


class GoogleLoginRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id_token: str = Field(min_length=32, max_length=8192)


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    role: str
    org_id: str
    home_path: str

    @classmethod
    def from_auth(cls, access_token: str, expires_in: int, role: str, org_id: str) -> "LoginResponse":
        return cls(
            access_token=access_token,
            expires_in=expires_in,
            role=role,
            org_id=org_id,
            home_path=home_path_for_role(role),
        )
