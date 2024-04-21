from dataclasses import dataclass
from enum import Enum


class TroveStatNames(Enum):
    maximum_health = "Maximum Health"
    bonus_maximum_health = "Maximum Health"
    health_regen = "Health Regen"
    bonus_health_regen = "Health Regen Bonus"
    neutral_damage = "Damage"
    bonus_neutral_damage = "Damage Bonus"
    physical_damage = "Physical Damage"
    bonus_physical_damage = "Physical Damage Bonus"
    magic_damage = "Magic Damage"
    bonus_magic_damage = "Magic Damage Bonus"
    critical_hit = "Critical Hit"
    bonus_critical_hit = "Critical Hit Bonus"
    critical_damage = "Critical Damage"
    bonus_critical_damage = "Critical Damage Bonus"
    light = "Light"
    bonus_light = "Light Bonus"
    attack_speed = "Attack Speed"
    movement_speed = "Movement Speed"
    jump = "Jump"
    stability = "Stability"
    magic_find = "Magic Find"
    bonus_magic_find = "Magic Find Bonus"


class TroveStats(Enum):
    maximum_health = 1 << 0
    bonus_maximum_health = 1 << 1
    health_regen = 1 << 2
    bonus_health_regen = 1 << 3
    neutral_damage = 1 << 4
    bonus_neutral_damage = 1 << 5
    physical_damage = 1 << 6
    bonus_physical_damage = 1 << 7
    magic_damage = 1 << 8
    bonus_magic_damage = 1 << 9
    critical_hit = 1 << 10
    bonus_critical_hit = 1 << 11
    critical_damage = 1 << 12
    bonus_critical_damage = 1 << 13
    light = 1 << 14
    bonus_light = 1 << 15
    attack_speed = 1 << 16
    movement_speed = 1 << 17
    jump = 1 << 18
    stability = 1 << 19
    magic_find = 1 << 20
    bonus_magic_find = 1 << 21


class TroveStatBonus(Enum):
    maximum_health = False
    bonus_maximum_health = True
    health_regen = False
    bonus_health_regen = True
    neutral_damage = False
    bonus_neutral_damage = True
    physical_damage = False
    bonus_physical_damage = True
    magic_damage = False
    bonus_magic_damage = True
    critical_hit = False
    bonus_critical_hit = True
    critical_damage = False
    bonus_critical_damage = True
    light = False
    bonus_light = True
    attack_speed = False
    movement_speed = False
    jump = False
    stability = False
    magic_find = False
    bonus_magic_find = True


@dataclass
class TroveStat:
    _id: int
    _value: float

    @classmethod
    def create(cls, stat_id, value):
        return cls(1 << stat_id, value)

    def __float__(self):
        return self._value

    def __gt__(self, other):
        if not isinstance(other, TroveStat):
            raise ValueError("Cannot compare TroveStat with non-TroveStat")
        if self.id != other.id:
            raise ValueError("Cannot compare TroveStat with different stat")
        return self._value > other._value

    def __lt__(self, other):
        if not isinstance(other, TroveStat):
            raise ValueError("Cannot compare TroveStat with non-TroveStat")
        if self.id != other.id:
            raise ValueError("Cannot compare TroveStat with different stat")
        return self._value < other._value

    def __eq__(self, other):
        if not isinstance(other, TroveStat):
            raise ValueError("Cannot compare TroveStat with non-TroveStat")
        if self.id != other.id:
            raise ValueError("Cannot compare TroveStat with different stat")
        return self._value == other._value

    def __ne__(self, other):
        if not isinstance(other, TroveStat):
            raise ValueError("Cannot compare TroveStat with non-TroveStat")
        if self.id != other.id:
            raise ValueError("Cannot compare TroveStat with different stat")
        return self._value != other._value

    def __ge__(self, other):
        if not isinstance(other, TroveStat):
            raise ValueError("Cannot compare TroveStat with non-TroveStat")
        if self.id != other.id:
            raise ValueError("Cannot compare TroveStat with different stat")
        return self._value >= other._value

    def __le__(self, other):
        if not isinstance(other, TroveStat):
            raise ValueError("Cannot compare TroveStat with non-TroveStat")
        if self.id != other.id:
            raise ValueError("Cannot compare TroveStat with different stat")
        return self._value <= other._value

    def __add__(self, other):
        if not isinstance(other, TroveStat):
            raise ValueError("Cannot add TroveStat with non-TroveStat")
        if self.id != other.id:
            raise ValueError("Cannot add TroveStat with different stat")
        return TroveStat(self._id, self._value + other._value)

    def __sub__(self, other):
        if not isinstance(other, TroveStat):
            raise ValueError("Cannot subtract TroveStat with non-TroveStat")
        if self.id != other.id:
            raise ValueError("Cannot subtract TroveStat with different stat")
        return TroveStat(self._id, self._value - other._value)

    def __mul__(self, other):
        if not isinstance(other, TroveStat):
            raise ValueError("Cannot multiply TroveStat with non-TroveStat")
        if self.id != other.id:
            raise ValueError("Cannot multiply TroveStat with different stat")
        return TroveStat(self._id, self._value * other._value)

    def __truediv__(self, other):
        if not isinstance(other, TroveStat):
            raise ValueError("Cannot divide TroveStat with non-TroveStat")
        if self.id != other.id:
            raise ValueError("Cannot divide TroveStat with different stat")
        return TroveStat(self._id, self._value / other._value)

    @property
    def id(self):
        return self._id

    @property
    def value(self):
        return round(self._value, 2)

    @property
    def is_bonus(self):
        return TroveStatBonus[self.stat_string_id].value

    @property
    def value_str(self):
        return str(self.value) + ("%" if self.is_bonus else "")

    @property
    def stat_string_id(self):
        return TroveStats(self._id).name

    @property
    def stat_name(self):
        return TroveStatNames[self.stat_string_id].value

    @property
    def stat_str(self):
        return f"{self.value_str} {self.stat_name}"


stat_1 = TroveStat.create(7, 540)
stat_2 = TroveStat.create(7, 540)
