import asyncio
from enum import Enum
from json import loads
from pathlib import Path
from typing import Optional

from flet import ThemeMode
from pydantic import BaseModel, Field, PrivateAttr, validator

from models.config import Locale


class AccentColor(Enum):
    blue = "BLUE"
    red = "RED"
    pink = "PINK"
    purple = "PURPLE"
    indigo = "INDIGO"
    cyan = "CYAN"
    teal = "TEAL"
    green = "GREEN"
    lime = "LIME"
    yellow = "YELLOW"
    amber = "AMBER"
    orange = "ORANGE"
    brown = "BROWN"

    def __str__(self):
        return self.value


class DismissableContent(BaseModel):
    terms_of_service: bool = False
    performance_mode: bool = False
    advanced_mode: bool = False


class Directories(BaseModel):
    extract_from: Optional[Path] = None
    extract_to: Optional[Path] = None
    changes_from: Optional[Path] = None
    changes_to: Optional[Path] = None


class ModManagerPreferences(BaseModel):
    page_size: int = 8
    custom_directories: list[tuple[str, Path]] = Field(default_factory=list)
    show_previews: bool = False
    auto_fix_mod_names: bool = True
    auto_generate_and_fix_cfg: bool = True

    @validator("custom_directories")
    def clean_custom_directories(cls, value):
        return [(n, d) for n, d in value if d.exists()]


class ModdersToolsPreferences(BaseModel):
    project_path: Optional[Path] = None


class Preferences(BaseModel):
    _page = PrivateAttr()
    path: Path
    web: bool = False
    locale: Locale = Locale.American_English
    theme: ThemeMode = Field(default=ThemeMode.DARK)
    accent_color: AccentColor = AccentColor.amber
    fullscreen: bool = False
    window_size: tuple[int, int] = (1630, 950)
    advanced_mode: bool = False
    performance_mode: bool = False
    changes_name_format: str = "%Y-%m-%d %H-%M-%S $dir"
    directories: Directories = Field(default_factory=Directories)
    dismissables: DismissableContent = Field(default_factory=DismissableContent)
    mod_manager: ModManagerPreferences = Field(default_factory=ModManagerPreferences)
    modders_tools: ModdersToolsPreferences = Field(
        default_factory=ModdersToolsPreferences
    )

    @classmethod
    async def load_from_web(cls, page):
        try:
            pref_obj = await page.client_storage.get_async("preferences", None)
            if not pref_obj:
                raise Exception("Missing preferences on client")
            pref = cls.parse_obj(pref_obj)
        except:
            pref = cls(path=Path("data/preferences.json"), web=True)
        pref.bind_page(page)
        pref.save()
        return pref

    @classmethod
    def load_from_json(cls, path: Path, page):
        if not path.exists():
            pref = cls(path=path)
        else:
            try:
                data = loads(path.read_text())
                pref = cls.parse_obj(data)
            except Exception:
                print(f"Failed to load preferences from {path}")
                pref = cls(path=path)
        pref.bind_page(page)
        pref.save()
        return pref

    def bind_page(self, page):
        self._page = page

    def save(self):
        self.path.parent.mkdir(exist_ok=True, parents=True)
        if not self.web:
            with open(self.path, "w+") as f:
                f.write(self.json())
        else:
            asyncio.create_task(self.save_web())

    async def save_web(self):
        try:
            await self._page.client_storage.set_async("preferences", self.json())
        except:
            ...
