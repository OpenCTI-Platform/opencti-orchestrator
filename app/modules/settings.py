from typing import List, Literal
from pydantic import root_validator
from app.core.settings import CustomBaseSettings
from app.modules.broker import BROKER_TYPES


class FlaskSettings(CustomBaseSettings):
    # DB Settings
    ELASTICSEARCH_HOST: str | List[str]
    ELASTICSEARCH_HTTP_AUTH: str = None
    # Heartbeat
    HEARTBEAT_INTERVAL: int = 10  # interval in seconds
    # Broker Settings
    BROKER: Literal[BROKER_TYPES] = "RabbitMQ"
    RABBITMQ_HOST: str
    RABBITMQ_PORT: int = 5672
    RABBITMQ_USER: str
    RABBITMQ_PASSWORD: str
    # Scheduler Settings
    SCHEDULER_API_ENABLED: bool = False
    SCHEDULER_JOBSTORES: dict = {"apscheduler.jobstores.default": {}}
    SCHEDULER_EXECUTORS: dict = {"default": {"type": "threadpool", "max_workers": 20}}
    SCHEDULER_JOB_DEFAULTS: dict = {"coalesce": False, "max_instances": 3}
    REDIS_HOST: str
    REDIS_PORT: int = 6379

    @root_validator
    def pre_convert_redis_to_scheduler_settings(cls, values: dict):
        host = values.get("REDIS_HOST")
        port = values.get("REDIS_PORT")
        if not host or not port:
            raise ValueError("Missing Redis host and port settings")

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
