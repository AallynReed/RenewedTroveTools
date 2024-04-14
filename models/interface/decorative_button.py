from flet import IconButton, Row, Icon


class RTTIconDecoButton(IconButton):
    def __init__(self, icon, icon_color=None, text=None, **kwargs):
        kwargs["on_click"] = kwargs.get("on_click", lambda x: x)
        kwargs["content"] = kwargs.get(
            "content",
            Row(controls=[Icon(icon, color=icon_color), *([text] if text else [])]),
        )
        kwargs["disabled"] = kwargs.get("disabled", True)
        super().__init__(**kwargs)
