import json
from pathlib import Path
from typing import List, Any, Dict

import yaml
from pydantic import BaseSettings


class FlaskSettings(BaseSettings):
    ELASTICSEARCH_HOST: str | List[str]
    ELASTICSEARCH_HTTP_AUTH: str = None
    SCHEDULER_API_ENABLED: bool = False
    BROKER: str = "RabbitMQ"
    RABBITMQ_HOST: str
    RABBITMQ_USER: str
    RABBITMQ_PASSWORD: str

    class Config:
        @classmethod
        def customise_sources(
            cls,
            init_settings,
            env_settings,
            file_secret_settings,
        ):
            return (
                init_settings,
                yml_config_setting,
                # json_config_setting,
                env_settings,
                file_secret_settings,
            )


def yml_config_setting(settings: BaseSettings) -> Dict[str, Any]:
    encoding = settings.__config__.env_file_encoding
    path = Path("config.yml")
    content = {}
    if path.exists():
        with open(path, "r", encoding=encoding) as f:
            content = yaml.safe_load(f)
    return content


#
# def json_config_setting(settings: BaseSettings) -> Dict[str, Any]:
#     encoding = settings.__config__.env_file_encoding
#     path = Path('config.json')
#     content = {}
#     if path.exists():
#         content = json.loads(Path('config.json').read_text(encoding))
#     return content
