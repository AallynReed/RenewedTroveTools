from datetime import datetime, timedelta
from pytz import UTC
from dataclasses import dataclass
from typing import Optional


@dataclass
class CrannyItem:
    name: str
    weeks: list[list[datetime]]
    price: int
    ally: bool
    currency: Optional[str]


class Cranny:
    def __init__(self):
        self.first_cranny = datetime(2023, 3, 7, tzinfo=UTC)
        self.week_length = timedelta(weeks=1)
        self.cranny_lifetime_int = 4
        self.cranny_lifetime = self.week_length * self.cranny_lifetime_int

    def current_cranny_timeline(self):
        now = datetime.now().astimezone(UTC)
        cranny_epoch = (now - self.first_cranny).total_seconds()
        crannies_passed, cranny_progress = divmod(
            cranny_epoch,
            self.cranny_lifetime.total_seconds()
        )
        start = self.first_cranny + timedelta(
            seconds=self.cranny_lifetime.total_seconds() * crannies_passed
        )
        end = start + self.cranny_lifetime
        ally_week = crannies_passed % 2
        weeks = []
        for i in range(self.cranny_lifetime_int):
            weeks.append(
                [
                    start + self.week_length * i,
                    start + self.week_length * (i + 1)
                ]
            )
        return start, end, weeks, bool(ally_week)

    def get_items(self):
        start, end, cranny_weeks, ally_week = self.current_cranny_timeline()
        items = []
        item_patterns = [
            ["First", [0, 1, 2, 3], "cubits"],
            ["Second", [0, 3], "credits"],
            ["Third", [0, 1], "credits"],
            ["Fourth", [1, 2], "credits"],
            ["Fifth", [2, 3], "credits"],
            ["Sixth", [0, 1, 2, 3], None],
        ]
        for name, pattern_weeks, cur in item_patterns:
            weeks = []
            price = 0
            for pattern_week in pattern_weeks:
                weeks.append(cranny_weeks[pattern_week])
            if cur is not None:
                if ally_week:
                    price = 500
                else:
                    price = 1000
                if cur == "cubits":
                    price *= 10
            items.append(
                CrannyItem(
                    name=name,
                    weeks=weeks,
                    price=price,
                    ally=ally_week,
                    currency=cur
                )
            )
        return items
