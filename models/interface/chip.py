from flet import Chip, BorderSide


class RTTChip(Chip):
    def __init__(self, **kwargs):
        kwargs["on_click"] = kwargs.get("on_click", lambda x: x)
        kwargs["border_side"] = kwargs.get("border_side", BorderSide(width=4))
        super().__init__(**kwargs)
