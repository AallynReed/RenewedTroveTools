from flet import (
    Column,
    Row,
    ResponsiveRow,
    Text,
    Image,
    Icon,
    icons,
    MainAxisAlignment,
    CrossAxisAlignment,
)


class HomeWidget(Column):
    def __init__(
        self,
        image=None,
        icon=None,
        title=None,
        title_size: int = 16,
        controls=None,
        column_spacing=None,
        responsive=False,
        **kwargs
    ):
        super().__init__(
            controls=[
                Row(
                    controls=[
                        Image(src=image, width=16, visible=bool(image)),
                        Icon(icon, size=16, visible=bool(icon)),
                        Text(title, size=title_size, visible=bool(title)),
                    ],
                    vertical_alignment=CrossAxisAlignment.CENTER,
                ),
                (
                    Column(
                        controls=controls if controls else [], spacing=column_spacing
                    )
                    if not responsive
                    else ResponsiveRow(
                        controls=controls if controls else [], spacing=column_spacing
                    )
                ),
            ],
            **kwargs
        )

    def set_controls(self, controls):
        if isinstance(controls, list):
            self.controls[1].controls = controls
        else:
            self.controls[1].controls = [controls]
        return self
