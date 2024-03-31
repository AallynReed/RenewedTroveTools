from pydantic import BaseModel


class ProjectConfig(BaseModel):
    name: str
    authors: list[str]
    description: str
    tags: list[str]

    @property
    def authors_string(self):
        return ", ".join(self.authors)

    @property
    def type(self):
        return self.tags[0] if self.tags else "Not Selected"

    @property
    def sub_type(self):
        return self.tags[1] if len(self.tags) > 1 else None


class VersionConfig(BaseModel):
    version: str
    changes: str
