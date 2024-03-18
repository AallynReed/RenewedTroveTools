from models.interface import Controller
from flet import (
    Divider,
    Card,
    Text,
    TextStyle,
    Column,
    Row,
    Chip,
    Icon,
    Image,
    TextField,
    Container,
)
from flet_core import padding, MainAxisAlignment


class ModdersController(Controller):
    def setup_controls(self):
        self.main = Text("Modder Tools")

    def setup_events(self):
        pass
