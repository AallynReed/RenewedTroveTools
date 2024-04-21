from dataclasses import dataclass
from enum import Enum
from models.trove.models.gems import GemElement, GemRarity, GemTier
from models.trove.models.classes import Class, ClassType
from models.trove.models.weapons import Weapon
from typing import Optional


@dataclass
class GemBuildsConfig:
    _class: Class
    subclass: Optional[Class] = None
