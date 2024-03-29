from pydantic import BaseModel


class ProjectConfig(BaseModel):
    name: str
    authors: list[str]
    tags: list[str]
