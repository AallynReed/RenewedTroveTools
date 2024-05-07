from flet import Text, TextField, TextStyle
from utils.locale import loc
from i18n import t

from models.interface import Controller
from utils.functions import throttle
from utils.trove.mastery import mr_to_points, points_to_mr


class MasteryController(Controller):
    def setup_controls(self):
        self.points_input = TextField(
            label=loc("Mastery Points"), helper_style=TextStyle(color="red")
        )
        self.level_input = TextField(
            label=loc("Mastery Levels"), helper_style=TextStyle(color="red")
        )
        self.mastery_buffs = Text(loc("Mastery Buffs"))
        self.geode_buffs = Text(loc("Geode Mastery Buffs"))

    def setup_events(self):
        self.points_input.on_change = self.calculate_mastery
        self.level_input.on_change = self.calculate_mastery

    @throttle
    async def calculate_mastery(self, event=None):
        self.points_input.helper_text = ""
        self.level_input.helper_text = ""
        if event.control == self.points_input:
            if not event.control.value:
                self.level_input.value = None
            else:
                try:
                    points = int(self.points_input.value)
                except ValueError:
                    self.points_input.helper_text = loc("Invalid Number")
                else:
                    level, points, increment = points_to_mr(points)
                    if level > 1000 or (level == 1000 and points):
                        level = 1000
                        increment, points = mr_to_points(level)
                        self.points_input.value = str(points)
                        self.points_input.helper_text = t("errors.max_mastery_1000")
                    self.level_input.value = str(level)
                    self.get_buffs()
        elif event.control == self.level_input:
            if not event.control.value:
                self.points_input.value = None
            else:
                try:
                    levels = int(self.level_input.value)
                except ValueError:
                    self.level_input.helper_text = t("errors.invalid_number")
                else:
                    if levels > 1000:
                        levels = 1000
                        self.level_input.helper_text = t("errors.max_mastery_1000")
                    self.level_input.value = str(levels)
                    increment, points = mr_to_points(levels)
                    self.points_input.value = points
                    self.get_buffs()
        await self.page.update_async()

    def get_buffs(self):
        mastery_limit = 500
        geode_limit = 100
        if not self.level_input.value:
            self.mastery_buffs.value = f"{t('mastery.mastery_buffs')}\n"
            self.geode_buffs.value = f"{t('mastery.geode_mastery_buffs')}\n"
            return
        mastery_text = f"{t('mastery.mastery_buffs')}\n"
        geode_text = f"{t('mastery.geode_mastery_buffs')}\n"
        level = int(self.level_input.value)
        health = 0
        damage = 0
        power_rank = 0
        magic_find = 0
        for _ in range(level if level <= mastery_limit else mastery_limit):
            health += 0.6
            damage += 0.2
            power_rank += 4
        if level > 500:
            for _ in range(level - 500):
                power_rank += 1
                magic_find += 1
        mastery_text += f"\n{t('stats.Health Bonus')}: {round(health, 2)}%"
        mastery_text += f"\n{t('stats.Damage Bonus')}: {round(damage, 2)}%"
        mastery_text += f"\n{t('stats.Power Rank')}: {power_rank}"
        mastery_text += f"\n{t('stats.Magic Find')}: {magic_find}"
        self.mastery_buffs.value = mastery_text
        light = 0
        power_rank = 0
        for _ in range(level if level <= geode_limit else geode_limit):
            light += 10
            power_rank += 5
        geode_text += f"\n{t('stats.Light')}: {round(light, 2)}"
        geode_text += f"\n{t('stats.Power Rank')}: {round(power_rank, 2)}"
        self.geode_buffs.value = geode_text
