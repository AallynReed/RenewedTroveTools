from flet import Text

from models.interface import Controller


class ExtractorController(Controller):
    def setup_controls(self):
        self.main = Text("Hello")

    def setup_events(self):
        ...