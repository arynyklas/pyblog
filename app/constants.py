from pathlib import Path
from fastapi.templating import Jinja2Templates

from typing import List


app_dirpath: Path = Path(__file__).parent
parent_dirpath: Path = app_dirpath.parent

templates: Jinja2Templates = Jinja2Templates(
    directory = parent_dirpath / "templates"
)

image_extensions: List[str] = [
    "gif",
    "jpeg",
    "jpg",
    "png",
    "svg",
    "webp"
]
