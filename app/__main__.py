from uvicorn import run as run_uvicorn

from app import main_app, setup_app
from app.config import config


setup_app()


run_uvicorn(
    app = main_app,
    host = config.host,
    port = config.port
)
