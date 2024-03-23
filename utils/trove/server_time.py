from datetime import datetime, timedelta, timezone, UTC


class ServerTime:
    def __init__(self):
        self.trove_time = timedelta(hours=11)
        self.dragon_duration = timedelta(days=3)
        self.dragon_interval = timedelta(days=14)
        self.first_luxion = datetime(2024, 3, 1, tzinfo=UTC)
        self.first_corruxion = datetime(2024, 3, 8, tzinfo=UTC)

    def __str__(self):
        return self.now.strftime("%a, %b %d\t\t%H:%M")

    @property
    def now(self):
        return datetime.now(UTC) - self.trove_time

    # Luxion

    def _calculate_dragon(self, first):
        delta = self.now - first
        completed, current = divmod(
            int(delta.total_seconds()), int(self.dragon_interval.total_seconds())
        )
        next_luxion = first + (completed + 1) * self.dragon_interval
        return completed, next_luxion, current

    def is_dragon(self, first):
        return self._calculate_dragon(first)[2] < self.dragon_duration.total_seconds()

    def next_dragon(self, first):
        return self._calculate_dragon(first)[1]

    def until_next_dragon(self, first):
        return self.next_dragon(first) - self.now

    def previous_dragon(self, first):
        completed, next_dragon, current = self._calculate_dragon(first)
        return next_dragon - self.dragon_interval

    def end_dragon(self, first):
        if self.is_dragon(first):
            return self.previous_dragon(first) + self.dragon_duration
        else:
            return self.next_dragon(first) + self.dragon_duration

    def until_end_dragon(self, first):
        return self.end_dragon(first) - self.now
