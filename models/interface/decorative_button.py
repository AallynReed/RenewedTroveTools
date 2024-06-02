from flet import IconButton, Row, Icon
from models.interface.image import RTTImage


class RTTIconDecoButton(IconButton):
    def __init__(
        self, icon=None, icon_color=None, image=None, size=24, text=None, **kwargs
    ):
        kwargs["on_click"] = kwargs.get("on_click", lambda x: x)
        kwargs["content"] = kwargs.get(
            "content",
            Row(
                controls=[
                    *(
                        [Icon(icon, color=icon_color, size=size)]
                        if icon is not None
                        else []
                    ),
                    *(
                        [RTTImage(src=image, width=size, height=size)]
                        if image is not None
                        else []
                    ),
                    *([text] if text else []),
                ],
                spacing=0,
                alignment="center",
            ),
        )
        kwargs["disabled"] = kwargs.get("disabled", True)
        super().__init__(**kwargs)
