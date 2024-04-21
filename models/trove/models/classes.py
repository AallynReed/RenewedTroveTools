from enum import Enum
from pydantic import BaseModel


class Class(Enum):
    bard = "Bard"
    boomeranger = "Boomeranger"
    candy_barbarian = "Candy Barbarian"
    chloromancer = "Chloromancer"
    dino_tamer = "Dino Tamer"
    dracolyte = "Dracolyte"
    fae_trickster = "Fae Trickster"
    gunslinger = "Gunslinger"
    ice_sage = "Ice Sage"
    knight = "Knight"
    lunar_lancer = "Lunar Lancer"
    neon_ninja = "Neon Ninja"
    pirate_captain = "Pirate Captain"
    revenant = "Revenant"
    shadow_hunter = "Shadow Hunter"
    solarion = "Solarion"
    tomb_raiser = "Tomb Raiser"
    vanguardian = "Vanguardian"


class ClassType(Enum):
    magic = "Magic"
    physical = "Physical"


class ClassAttributes(Enum):
    infinite_attackspeed = "Infinite Attack Speed"


class TroveClass(BaseModel): ...
