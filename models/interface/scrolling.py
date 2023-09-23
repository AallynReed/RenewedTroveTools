import flet as ft


class ScrollingFrame(ft.UserControl):
    def __init__(self, content, vertical_scrollbar_always_visible=True, expand=True, **kwargs):
        super().__init__(expand=expand, **kwargs)

        self.content_control = content
        self.vertical_scrollbar_always_visible = vertical_scrollbar_always_visible

    def build(self):
        first_dimension = ft.Column if self.vertical_scrollbar_always_visible else ft.Row
        second_dimension = ft.Row if self.vertical_scrollbar_always_visible else ft.Column

        scroller = first_dimension(
            [other_direction := second_dimension([ft.Container(self.content_control)])],
        )

        scroller.scroll = ft.ScrollMode.AUTO
        other_direction.scroll = ft.ScrollMode.AUTO

        return scroller
