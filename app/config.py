from pydantic import BaseModel
from pathlib import Path
from yaml import load as load_yaml, Loader as YAMLLoader

from app.constants import app_dirpath

from typing import List


CONFIG_FILEPATH: Path = app_dirpath / "config.yml"


class DBConfig(BaseModel):
    uri: str
    name: str


class UserLimitsConfig(BaseModel):
    text_length: int


class Config(BaseModel):
    class Config:
        arbitrary_types_allowed: bool = True

    version: str
    host: str
    port: int
    db: DBConfig
    secret: str
    secrets_lifetime: int
    verifications_lifetime: int
    user_limits: UserLimitsConfig
    reactions_keys: List[str]
    api_posts_limit: int


with CONFIG_FILEPATH.open("r", encoding="utf-8") as file:
    config_data: dict = load_yaml(
        stream = file,
        Loader = YAMLLoader
    )


config: Config = Config(
    user_limits = UserLimitsConfig(
        **config_data.pop("user_limits")
    ),
    **config_data
)
