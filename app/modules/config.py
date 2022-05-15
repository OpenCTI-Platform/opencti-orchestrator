from pathlib import Path
from typing import List, Any, Dict
from apscheduler.jobstores.redis import RedisJobStore
import yaml
from pydantic import BaseSettings, root_validator


class FlaskSettings(BaseSettings):
    # DB Settings
    ELASTICSEARCH_HOST: str | List[str]
    ELASTICSEARCH_HTTP_AUTH: str = None
    # Broker Settings
    BROKER: str = "RabbitMQ"
    RABBITMQ_HOST: str
    RABBITMQ_PORT: int = 5672
    RABBITMQ_USER: str
    RABBITMQ_PASSWORD: str
    # Scheduler Settings
    SCHEDULER_API_ENABLED: bool = False
    SCHEDULER_JOBSTORES: dict = {
        "apscheduler.jobstores.default": {}
    }
    SCHEDULER_EXECUTORS: dict = {
        "default": {
            "type": "threadpool", "max_workers": 20
        }
    }
    SCHEDULER_JOB_DEFAULTS: dict = {
        "coalesce": False,
        "max_instances": 3
    }
    REDIS_HOST: str
    REDIS_PORT: int

    @root_validator
    def pre_convert_redis_to_scheduler_settings(cls, values: dict):
        host = values.get('REDIS_HOST')
        port = values.get('REDIS_PORT')
        if not host or not port:
            raise ValueError("Missing Redis host and port settings")

        values['SCHEDULER_JOBSTORES'] = {
            "apscheduler.jobstores.default": {
                "type": "redis",
                "jobs_key": "orchestrator_jobs",
                "run_times_key": "orchestrator_runs",
                "host": host,
                "port": port
            }
        }
        return values


    # @validator("regex_patterns", "filter_config", pre=True)
    # def pre_convert_redis_to_scheduler_seetings(cls, field: str) -> Any:
    #     return list(filter(None, (x.strip() for x in field.splitlines())))


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
