from pydantic import BaseModel


class LoginIn(BaseModel):
    password: str


class VisibilidadeIn(BaseModel):
    deleted: bool