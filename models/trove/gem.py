"""
The accuracy in this code was possible due to the great help of SummerHaas (Summer#9392)
Huge thanks to them for explaining and helping me understand gems to a much deeper level.

The code below attempts to simulate how gems work internally in the game in a much more
accurate manner, simulating the existing containers and possible overflows that occur.

While not possible to see through the sugar-coated interface in-game it will allow for
power rank data to be accurate as well as stats and augmentation percentages.

Thanks again Summer for the information you shared.

Here's some content Summer works on with other Trovians
https://trove.summerhaas.com/ Make sure to check out their incredible work.
"""

from __future__ import annotations

import base64
from copy import copy
from enum import Enum
from json import loads
from random import randint, choice
from typing import Any
from uuid import UUID, uuid4

from i18n import t
from pydantic import BaseModel, Field

from models.trove.gems import (
    max_levels,
    stat_multipliers,
    gem_min_max,
    gem_container_pr,
    level_increments,
)
from utils.functions import split_boosts


# This dictates the percentages stats can generate at.
# This adds complexity in a way but system remains unchanged progression wise.
GEM_COMPLEXITY = 40 * 40


class Stat(Enum):
    """This class enumerates the various stats available in gems."""

    light = "Light"
    physical_damage = "Physical Damage"
    magic_damage = "Magic Damage"
    critical_damage = "Critical Damage"
    critical_hit = "Critical Hit"
    maximum_health = "Maximum Health"
    maximum_health_per = "Maximum Health %"


excluded_stats = {Stat.light, Stat.physical_damage, Stat.magic_damage}
all_gem_stats = [s for s in Stat if s not in excluded_stats]
arcane_gem_stats = all_gem_stats + [Stat.magic_damage]
fierce_gem_stats = all_gem_stats + [Stat.physical_damage]
empowered_gem_stats = all_gem_stats + [Stat.physical_damage, Stat.magic_damage]


class GemStatContainer(BaseModel):
    """This class simulates a stat container."""

    base: int
    rough: int
    precise: int
    superior: int

    @property
    def total(self) -> int:
        ratio = GEM_COMPLEXITY / 40
        return sum(
            [
                self.base,
                self.rough * ratio,
                self.precise * ratio * 2,
                self.superior * ratio * 5,
            ]
        )

    @property
    def percentage(self) -> float:
        if not self.total:
            return 0
        return self.total / GEM_COMPLEXITY


class GemStat(BaseModel):
    """This class simulates a stat in a gem."""

    uuid: UUID = Field(default_factory=uuid4)
    name: Stat
    gem: BaseModel
    containers: list[GemStatContainer]

    def __eq__(self, other) -> bool:
        return self.uuid == getattr(other, "uuid", None)

    def __ne__(self, other) -> bool:
        return not self.__eq__(other)

    @property
    def boosts(self) -> int:
        """This property returns the amount of extra containers."""

        return len(self.containers) - 1

    @property
    def max_augments(self) -> int:
        """This property calculates the maximum amount of augments a gem can hold"""

        return GEM_COMPLEXITY + GEM_COMPLEXITY * self.boosts

    @property
    def current_augments(self) -> int:
        """This property calculates the current amount of augments in place"""

        augmented = sum(c.total for c in self.containers)
        return min(augmented, self.max_augments)

    @property
    def percentage(self) -> float:
        """This property calculates true percentage of gem while respecting each
        containers' overflow

        Since each container can exceed 100% this will allow that to happen
        Counting from first to last container the amount of boosts
        While limiting the amount of boosts dynamically through boost count"""

        percentage = 0
        if self.current_augments:
            percentage = self.current_augments / self.max_augments
        return min(1, percentage)

    @property
    def display_percentage(self) -> float:
        """This method returns the percentage for display in a 100% manner."""

        return round(self.percentage * 100, 2)

    def get_values(self):
        """Returns the calculated values for the current stat."""

        min_val, max_val = stat_multipliers[self.gem.tier.name][self.name.value]
        min_inc, max_inc = gem_min_max[self.gem.tier.name][self.name.value][
            self.gem.type.name
        ]
        # Get initial stats
        stat_output = [0, 0]
        stat_output[0] = min_inc * min_val
        stat_output[1] = max_inc * max_val
        power_rank = 0
        # Calculate level stats
        for l, _ in enumerate(range(self.gem.level), 1):
            level_increment = level_increments[self.gem.tier.name](l)
            power_rank += level_increment
            stat_output[0] += level_increment * min_val
            stat_output[1] += level_increment * max_val
        min_container_pr, max_container_pr = gem_container_pr[self.gem.type.name][
            self.gem.tier.name
        ]
        container_pr = (
            min_container_pr + (max_container_pr - min_container_pr) * self.percentage
        )
        power_rank += container_pr
        # Calculate boosts
        for boost in range(self.boosts):
            power_rank += container_pr
            stat_output[0] += min_inc * min_val
            stat_output[1] += max_inc * max_val
        min_stat = round(stat_output[0], 2)
        max_stat = round(stat_output[1], 2)
        return min_stat, max_stat, round(max_stat - min_stat, 2), power_rank

    @property
    def min_value(self):
        """Returns the calculated value of the 100% augmentation value."""

        return self.get_values()[0]

    @property
    def max_value(self):
        """Returns the calculated value of the 0% augmentation value."""

        return self.get_values()[1]

    @property
    def difference_value(self):
        """Returns the calculated difference between 0% and 100% augmentation values."""

        return self.get_values()[2]

    @property
    def value(self):
        """Returns the calculated stat value."""

        return self.min_value + self.difference_value * self.percentage

    @property
    def power_rank(self):
        """Returns the calculated power rank of the gem."""

        return self.get_values()[3]

    @property
    def is_maxed(self) -> bool:
        """Returns a boolean value indicating whether gem has max augmentation or not."""

        return self.percentage == 1

    def zero_augments(self) -> None:
        """Make all augments zero base on all containers"""

        for container in self.containers:
            container.base = 0
            container.rough = 0
            container.precise = 0
            container.superior = 0

    def reset_augments(self) -> None:
        """Remove all augments from all the containers"""

        for container in self.containers:
            container.rough = 0
            container.precise = 0
            container.superior = 0

    def add_boost(self) -> None:
        """Generate a new container"""

        self.containers.append(
            GemStatContainer(
                **{
                    "base": randint(0, GEM_COMPLEXITY),
                    "rough": 0,
                    "precise": 0,
                    "superior": 0,
                }
            )
        )

    def remove_boost(self) -> None:
        """Remove the last container."""

        self.containers.remove(self.containers[-1])

    def move_boost_to(self, stat) -> None:
        """Put the last container into another stat."""

        container = self.containers[-1]
        self.containers.remove(container)
        stat.containers.append(container)

    def add_rough_focus(self) -> bool:
        """Adds a rough focus to the first container under max augments."""

        for container in self.containers:
            if container.total < GEM_COMPLEXITY:
                container.rough += 1
                break
        return self.is_maxed

    def add_precise_focus(self) -> bool:
        """Adds a precise focus to the first container under max augments."""

        for container in self.containers:
            if container.total < GEM_COMPLEXITY:
                container.precise += 1
                break
        return self.is_maxed

    def add_superior_focus(self) -> bool:
        """Adds a superior focus to the first container under max augments."""

        for container in self.containers:
            if container.total < GEM_COMPLEXITY:
                container.superior += 1
                break
        return self.is_maxed

    @classmethod
    def random(cls, name: str, boosts: int, gem: Gem) -> GemStat:
        stat = cls(
            name=name,
            gem=gem,
            containers=[
                GemStatContainer(
                    **{
                        "base": randint(0, GEM_COMPLEXITY),
                        "rough": 0,
                        "precise": 0,
                        "superior": 0,
                    }
                )
                for _ in range(boosts + 1)
            ],
        )
        return stat

    @classmethod
    def maxed(cls, name: str, boosts: int, gem: Gem) -> GemStat:
        stat = cls.random(name, boosts, gem)
        # Just keep adding boosts to a randomly generated gem
        # This way a gem can be "downgraded" into being low level again
        while not stat.is_maxed:
            stat.add_rough_focus()
        return stat


class GemTier(Enum):
    radiant = "radiant"
    stellar = "stellar"
    crystal = "crystal"


class GemTierColor(Enum):
    radiant = "#dff6ff"
    stellar = "#f0e62a"
    crystal = "#77e4ac"


class GemType(Enum):
    lesser = "Lesser"
    empowered = "Empowered"


class GemElement(Enum):
    fire = "Fire"
    water = "Water"
    air = "Air"
    cosmic = "Cosmic"


class GemColor(Enum):
    fire = "ff3434"
    water = "22e9ff"
    air = "ffe34f"
    cosmic = "125353"


class GemRestriction(Enum):
    arcane = "Arcane"
    fierce = "Fierce"


class ElementalGemAbility(Enum):
    explosive_epilogue = "Explosive Epilogue"
    volatile_velocity = "Volatile Velocity"
    cubic_curtain = "Cubic Curtain"
    mired_mojo = "Mired Mojo"
    pyrodisc = "Pyrodisc"
    stunburst = "Stunburst"
    spirit_surge = "Spirit Surge"
    stinging_curse = "Stinging Curse"


class CosmicGemAbility(Enum):
    berseker_battler = "Berserker Battler"
    flower_power = "Flower Power"
    empyrean_barrier = "Empyrean Barrier"
    vampirian_vanquisher = "Vampirian Vanquisher"


class Gem(BaseModel):
    uuid: UUID = Field(default_factory=uuid4)
    level: int
    tier: GemTier
    type: GemType
    element: GemElement
    stats: list[GemStat]

    def __eq__(self, other):
        return self.uuid == getattr(other, "uuid", None)

    def __ne__(self, other):
        return not self.__eq__(other)

    @property
    def pseudo_name(self):
        return t(
            "gem_full_names." + " ".join([self.type.value, self.element.value, "Gem"])
        )

    @property
    def max_level(self):
        return max_levels[self.tier.name]

    @property
    def power_rank(self):
        return sum([s.power_rank for s in self.stats]) + (
            0 if self.type == GemType.lesser else 100
        )

    @property
    def color(self):
        return GemColor[self.element.name]

    def set_level(self, level: int):
        self.level = level
        max_boosts = min(3, divmod(level, 5)[0])
        boosted_stats = [s for s in self.stats if s.boosts]
        current_boosts = sum([s.boosts for s in boosted_stats])
        difference = max_boosts - current_boosts
        if difference > 0:
            for i in range(abs(difference)):
                stat = choice(self.stats)
                stat.add_boost()
        elif difference < 0:
            for i in range(abs(difference)):
                stat = choice(boosted_stats)
                stat.remove_boost()
                boosted_stats = [s for s in self.stats if s.boosts]

    @classmethod
    def load_gem(cls, raw_data):
        data = loads(base64.b64decode(raw_data).decode("utf-8"))
        return cls(**data)

    def save_gem(self):
        return base64.b64encode(self.json().encode("utf-8"))


class LesserGem(Gem):
    restriction: GemRestriction

    @property
    def name(self):
        return t(
            "gem_full_names."
            + " ".join([self.restriction.value, self.element.value, "Gem"])
        )

    @classmethod
    def random_gem(cls, tier: GemTier = None, element: GemElement = None):
        tier = tier or choice([c for c in GemTier])
        level = 1
        type = GemType.lesser
        element = element or choice([c for c in GemElement])
        restriction = choice([c for c in GemRestriction])
        stat_names = generate_gem_stats(type, restriction, element)
        boosts = split_boosts(min(3, divmod(level, 5)[0]))
        gem = cls(
            level=level,
            tier=tier,
            type=type,
            element=element,
            stats=[],
            restriction=restriction,
        )
        for i, (stat_name, boost_count) in enumerate(zip(stat_names, boosts)):
            gem.stats.append(GemStat.random(stat_name, boost_count, gem))
        return gem

    def change_restriction(self, restriction: GemRestriction):
        self.restriction = restriction
        for stat in self.stats:
            if self.restriction == GemRestriction.arcane:
                if stat.name == Stat.physical_damage:
                    stat.name = Stat.magic_damage
            if self.restriction == GemRestriction.fierce:
                if stat.name == Stat.magic_damage:
                    stat.name = Stat.physical_damage

    def possible_change_stats(self, _: Stat):
        stats = []
        if self.restriction == GemRestriction.arcane:
            stats.extend(arcane_gem_stats)
        elif self.restriction == GemRestriction.fierce:
            stats.extend(fierce_gem_stats)
        for stat in self.stats:
            for pstat in copy(stats):
                if stat.name.value == pstat.value:
                    stats.remove(pstat)
        return stats


class EmpoweredGem(Gem):
    ability: Any = None

    @property
    def name(self):
        return t("gem_abilities." + self.ability.value)

    @property
    def possible_abilities(self):
        return (
            list(ElementalGemAbility)
            if self.element != GemElement.cosmic
            else list(CosmicGemAbility)
        )

    @classmethod
    def random_gem(cls, tier: GemTier = None, element: GemElement = None):
        tier = tier or choice([c for c in GemTier])
        level = 1
        type = GemType.empowered
        element = element or choice([c for c in GemElement])
        ability_set = (
            ElementalGemAbility if element != GemElement.cosmic else CosmicGemAbility
        )
        ability = choice(list(ability_set))
        stat_names = generate_gem_stats(type, None, element)
        boosts = split_boosts(min(3, divmod(level, 5)[0]))
        gem = cls(
            level=level,
            tier=tier,
            type=type,
            element=element,
            stats=[],
            ability=ability,
        )
        for i, (stat_name, boost_count) in enumerate(zip(stat_names, boosts)):
            gem.stats.append(GemStat.random(stat_name, boost_count, gem))
        return gem

    def possible_change_stats(self, cstat: Stat):
        stats = []
        stats_in_use = [s.name for s in self.stats]
        damage_types = [Stat.magic_damage, Stat.physical_damage]
        for stat in empowered_gem_stats:
            if stat in stats_in_use:
                continue
            if cstat.name not in damage_types and stat in damage_types:
                for dstat in damage_types:
                    br = False
                    if dstat in stats_in_use:
                        br = True
                        break
                if br:
                    continue
            stats.append(stat)
        return stats


def generate_gem_stats(
    gem_type: GemType, restriction: GemRestriction, element: GemElement
):
    stats = []
    if gem_type == GemType.lesser:
        if restriction == GemRestriction.arcane:
            available_stats = arcane_gem_stats
        elif restriction == GemRestriction.fierce:
            available_stats = fierce_gem_stats
        if element == GemElement.cosmic:
            stats.append(Stat.light)
    elif gem_type == GemType.empowered:
        available_stats = empowered_gem_stats
        if element == GemElement.cosmic:
            stats.append(Stat.light)
    while len(stats) < 3:
        stat = choice(available_stats)
        if stat in stats:
            continue
        if stat == Stat.physical_damage and Stat.magic_damage in stats:
            continue
        if stat == Stat.magic_damage and Stat.physical_damage in stats:
            continue
        stats.append(stat)
    return stats
