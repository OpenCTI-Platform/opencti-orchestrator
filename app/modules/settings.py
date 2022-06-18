import logging
from typing import List, Literal
from pydantic import root_validator
from app.core.settings import CustomBaseSettings
from app.modules.broker import BROKER_TYPES

LOG_LEVELS = ("DEBUG_ALL",) + tuple(logging._levelToName.values())


class FlaskSettings(CustomBaseSettings):
    LOGGING: Literal[LOG_LEVELS] = "INFO"
    # OpenCTI
    OPENCTI_URL: str
    # DB Settings
    ELASTICSEARCH_URL: str | List[str]
    ELASTICSEARCH_HTTP_AUTH: str = None
    # Heartbeat
    HEARTBEAT_INTERVAL: int = 10  # interval in seconds
    # Broker Settings
    BROKER: Literal[BROKER_TYPES] = "RabbitMQ"
    RABBITMQ_HOSTNAME: str = None
    RABBITMQ_PORT: int = 5672
    RABBITMQ_USER: str = None
    RABBITMQ_PASSWORD: str = None
    # Scheduler Settings
    SCHEDULER_API_ENABLED: bool = False
    SCHEDULER_JOBSTORES: dict = {"apscheduler.jobstores.default": {}}
    SCHEDULER_EXECUTORS: dict = {"default": {"type": "threadpool", "max_workers": 20}}
    SCHEDULER_JOB_DEFAULTS: dict = {"coalesce": False, "max_instances": 3}
    REDIS_HOSTNAME: str
    REDIS_PORT: int = 6379

    @root_validator
    def pre_convert_redis_to_scheduler_settings(cls, values: dict):
        host = values.get("REDIS_HOSTNAME")
        port = values.get("REDIS_PORT")
        if not host or not port:
            raise ValueError("Missing Redis hostname and port settings")

        values["SCHEDULER_JOBSTORES"] = {
            "apscheduler.jobstores.default": {
                "type": "redis",
                "jobs_key": "orchestrator_jobs",
                "run_times_key": "orchestrator_runs",
                "host": host,
                "port": port,
            }
        }
        return values

    # @root_validator
    # def pre_broker_validator(cls, values: dict):
    #     if values.get("BROKER") == BROKER_TYPES.index(0)
