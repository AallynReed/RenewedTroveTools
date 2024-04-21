from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import (
    Any,
    Callable,
    ClassVar,
    Dict,
    Iterator,
    List,
    Optional,
    Tuple,
    Type,
    TypeVar,
    overload,
)

from typing_extensions import Self


class TroveStatNames(Enum):
    maximum_health = "Maximum Health"
    bonus_maximum_health = "Maximum Health"
    health_regen = "Health Regeneration"
    bonus_health_regen = "Health Regeneration Bonus"
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
    power_rank = "Power Rank"
    energy_regen = "Energy Regeneration"
    bonus_energy_regen = "Energy Regeneration Bonus"
    maximum_energy = "Maximum Energy"
    lasermancy = "Lasermancy"


class TroveStats(Enum):
    maximum_health = 1 << 1
    bonus_maximum_health = 1 << 2
    health_regen = 1 << 3
    bonus_health_regen = 1 << 4
    neutral_damage = 1 << 5
    bonus_neutral_damage = 1 << 6
    physical_damage = 1 << 7
    bonus_physical_damage = 1 << 8
    magic_damage = 1 << 9
    bonus_magic_damage = 1 << 10
    critical_hit = 1 << 11
    bonus_critical_hit = 1 << 12
    critical_damage = 1 << 13
    bonus_critical_damage = 1 << 14
    light = 1 << 15
    bonus_light = 1 << 16
    attack_speed = 1 << 17
    movement_speed = 1 << 18
    jump = 1 << 19
    stability = 1 << 20
    magic_find = 1 << 21
    bonus_magic_find = 1 << 22
    power_rank = 1 << 23
    energy_regen = 1 << 24
    bonus_energy_regen = 1 << 25
    maximum_energy = 1 << 26
    lasermancy = 1 << 27


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
    power_rank = False
    energy_regen = False
    bonus_energy_regen = True
    maximum_energy = False
    lasermancy = False


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
        if isinstance(other, (int, float)):
            self._value += other
            return self
        if not isinstance(other, TroveStat):
            raise ValueError("Cannot add TroveStat with non-TroveStat")
        if self.id != other.id:
            raise ValueError("Cannot add TroveStat with different stat")
        return TroveStat(self._id, self._value + other._value)

    def __sub__(self, other):
        if isinstance(other, (int, float)):
            self._value -= other
            return self
        if not isinstance(other, TroveStat):
            raise ValueError("Cannot subtract TroveStat with non-TroveStat")
        if self.id != other.id:
            raise ValueError("Cannot subtract TroveStat with different stat")
        return TroveStat(self._id, self._value - other._value)

    def __mul__(self, other):
        if isinstance(other, (int, float)):
            self._value *= other
            return self
        if not isinstance(other, TroveStat):
            raise ValueError("Cannot multiply TroveStat with non-TroveStat")
        if self.id != other.id:
            raise ValueError("Cannot multiply TroveStat with different stat")
        return TroveStat(self._id, self._value * other._value)

    def __truediv__(self, other):
        if isinstance(other, (int, float)):
            self._value /= other
            return self
        if not isinstance(other, TroveStat):
            raise ValueError("Cannot divide TroveStat with non-TroveStat")
        if self.id != other.id:
            raise ValueError("Cannot divide TroveStat with different stat")
        return TroveStat(self._id, self._value / other._value)

    def __repr__(self):
        return f"TroveStat({self.stat_name}={self._value})"

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


@dataclass
class StatsList:
    _value: int
    stats: Optional[List[TroveStat]] = None

    @classmethod
    def from_value(cls, value):
        stats = []
        for stat in reversed(TroveStats):
            if value & stat.value:
                stats.append(TroveStat.create(stat.value, 0))
        return cls(value, stats)

    @property
    def value(self):
        for stat in self.stats:
            self._value |= stat.id
        return self._value


print(
    StatsList(
        0,
        stats=[
            TroveStat.create(1, 0),
            TroveStat.create(12, 0),
            TroveStat.create(16, 0),
            TroveStat.create(17, 0),
            TroveStat.create(23, 0),
        ],
    ).value
)
print(StatsList.from_value(8589314))


BF = TypeVar("BF", bound="BaseFlags")


class flag_value:
    def __init__(self, func: Callable[[Any], int]):
        self.flag: int = func(None)
        self.__doc__: Optional[str] = func.__doc__

    @overload
    def __get__(self, instance: None, owner: Type[BF]) -> Self: ...

    @overload
    def __get__(self, instance: BF, owner: Type[BF]) -> bool: ...

    def __get__(self, instance: Optional[BF], owner: Type[BF]) -> Any:
        if instance is None:
            return self
        return instance._has_flag(self.flag)

    def __set__(self, instance: BaseFlags, value: bool) -> None:
        instance._set_flag(self.flag, value)

    def __repr__(self) -> str:
        return f"<flag_value flag={self.flag!r}>"


class alias_flag_value(flag_value):
    pass


def fill_with_flags(*, inverted: bool = False) -> Callable[[Type[BF]], Type[BF]]:
    def decorator(cls: Type[BF]) -> Type[BF]:
        # fmt: off
        cls.VALID_FLAGS = {
            name: value.flag
            for name, value in cls.__dict__.items()
            if isinstance(value, flag_value)
        }
        # fmt: on

        if inverted:
            max_bits = max(cls.VALID_FLAGS.values()).bit_length()
            cls.DEFAULT_VALUE = -1 + (2**max_bits)
        else:
            cls.DEFAULT_VALUE = 0

        return cls

    return decorator


class BaseFlags:
    VALID_FLAGS: ClassVar[Dict[str, int]]
    DEFAULT_VALUE: ClassVar[int]

    value: int

    __slots__ = ("value",)

    def __init__(self, **kwargs: bool):
        self.value = self.DEFAULT_VALUE
        for key, value in kwargs.items():
            if key not in self.VALID_FLAGS:
                raise TypeError(f"{key!r} is not a valid flag name.")
            setattr(self, key, value)

    @classmethod
    def _from_value(cls, value):
        self = cls.__new__(cls)
        self.value = value
        return self

    def __or__(self, other: Self) -> Self:
        return self._from_value(self.value | other.value)

    def __and__(self, other: Self) -> Self:
        return self._from_value(self.value & other.value)

    def __xor__(self, other: Self) -> Self:
        return self._from_value(self.value ^ other.value)

    def __ior__(self, other: Self) -> Self:
        self.value |= other.value
        return self

    def __iand__(self, other: Self) -> Self:
        self.value &= other.value
        return self

    def __ixor__(self, other: Self) -> Self:
        self.value ^= other.value
        return self

    def __invert__(self) -> Self:
        max_bits = max(self.VALID_FLAGS.values()).bit_length()
        max_value = -1 + (2**max_bits)
        return self._from_value(self.value ^ max_value)

    def __bool__(self) -> bool:
        return self.value != self.DEFAULT_VALUE

    def __eq__(self, other: object) -> bool:
        return isinstance(other, self.__class__) and self.value == other.value

    def __ne__(self, other: object) -> bool:
        return not self.__eq__(other)

    def __hash__(self) -> int:
        return hash(self.value)

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} value={self.value}>"

    def __iter__(self) -> Iterator[Tuple[str, bool]]:
        for name, value in self.__class__.__dict__.items():
            if isinstance(value, alias_flag_value):
                continue

            if isinstance(value, flag_value):
                yield (name, self._has_flag(value.flag))

    def _has_flag(self, o: int) -> bool:
        return (self.value & o) == o

    def _set_flag(self, o: int, toggle: bool) -> None:
        if toggle is True:
            self.value |= o
        elif toggle is False:
            self.value &= ~o
        else:
            raise TypeError(
                f"Value to set for {self.__class__.__name__} must be a bool."
            )


@fill_with_flags()
class TroveStatFlags(BaseFlags):
    @flag_value
    def maximum_health(self) -> int:
        return 1 << 1

    @flag_value
    def bonus_maximum_health(self) -> int:
        return 1 << 2

    @flag_value
    def health_regen(self) -> int:
        return 1 << 3

    @flag_value
    def bonus_health_regen(self) -> int:
        return 1 << 4

    @flag_value
    def neutral_damage(self) -> int:
        return 1 << 5

    @flag_value
    def bonus_neutral_damage(self) -> int:
        return 1 << 6

    @flag_value
    def physical_damage(self) -> int:
        return 1 << 7

    @flag_value
    def bonus_physical_damage(self) -> int:
        return 1 << 8

    @flag_value
    def magic_damage(self) -> int:
        return 1 << 9

    @flag_value
    def bonus_magic_damage(self) -> int:
        return 1 << 10

    @flag_value
    def critical_hit(self) -> int:
        return 1 << 11

    @flag_value
    def bonus_critical_hit(self) -> int:
        return 1 << 12

    @flag_value
    def critical_damage(self) -> int:
        return 1 << 13

    @flag_value
    def bonus_critical_damage(self) -> int:
        return 1 << 14

    @flag_value
    def light(self) -> int:
        return 1 << 15

    @flag_value
    def bonus_light(self) -> int:
        return 1 << 16

    @flag_value
    def attack_speed(self) -> int:
        return 1 << 17

    @flag_value
    def movement_speed(self) -> int:
        return 1 << 18

    @flag_value
    def jump(self) -> int:
        return 1 << 19

    @flag_value
    def stability(self) -> int:
        return 1 << 20

    @flag_value
    def magic_find(self) -> int:
        return 1 << 21

    @flag_value
    def bonus_magic_find(self) -> int:
        return 1 << 22

    @flag_value
    def power_rank(self) -> int:
        return 1 << 23

    @flag_value
    def energy_regen(self) -> int:
        return 1 << 24

    @flag_value
    def bonus_energy_regen(self) -> int:
        return 1 << 25

    @flag_value
    def maximum_energy(self) -> int:
        return 1 << 26

    @flag_value
    def lasermancy(self) -> int:
        return 1 << 27
