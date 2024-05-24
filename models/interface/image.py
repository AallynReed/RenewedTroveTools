from flet import Image
from pathlib import Path


class RTTImage(Image):
    def __init__(self, src=None, is_fallback=False, **kwargs):
        src = src or ""
        src = src.as_posix() if isinstance(src, Path) else src
        if src is not None and src.startswith("http") and not is_fallback:
            error_content = RTTImage(
                is_fallback=True,
                src="https://kiwiapi.slynx.xyz/v1/misc/assets/images/construction.png",
            )
            kwargs["error_content"] = error_content
        elif src is not None and not is_fallback:
            error_content = RTTImage("assets/" + src, is_fallback=True)
            kwargs["error_content"] = error_content
            src = "https://kiwiapi.slynx.xyz/v1/misc/assets/" + src
        elif src is None:
            raise ValueError("Missing src parameter")
        kwargs["src"] = src
        super().__init__(**kwargs)
