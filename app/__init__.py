import logging
import click
from flask.cli import with_appcontext
from flask_openapi3 import Info, OpenAPI
from pydantic.error_wrappers import ValidationError
from apscheduler.schedulers import (
    SchedulerAlreadyRunningError,
    SchedulerNotRunningError,
)
from app.modules.settings import FlaskSettings

# TODO add verification that the index exists
INDEX_NAME = "opencti_orchestrator"


def create_app(config_path: str, run_heartbeat: bool = True):
    info = Info(
        title="OpenCTI Orchestrator", version="1.0.0"
    )  # TODO get this version from setup.py
    app = OpenAPI(__name__, info=info)

    try:
        app.config.from_object(FlaskSettings(_yaml_file=config_path))
    except ValidationError as e:
        app.logger.error(e)
        return None

    logging_level = app.config.get("LOGGING")
    logging.basicConfig(level=logging_level)
    if logging_level != "DEBUG_ALL":
        elastic_logger = logging.getLogger("elasticsearch")
        elastic_logger.setLevel(logging.CRITICAL)
        schedule_logger = logging.getLogger("apscheduler")
        schedule_logger.setLevel(logging.CRITICAL)

    try:
        initialize_extensions(app)
    except ValueError as e:
        app.logger.error(f"{e}")
        return None

    register_blueprints(app)
    # appcontext_tearing_down.connect(shutdown)
    if run_heartbeat:
        setup_heartbeat()

    return app


def initialize_extensions(app):
    from app.extensions import elastic, scheduler, broker

    try:
        elastic.init_app(app)
    except ValueError as e:
        raise ValueError(f"Error to contact elasticsearch server {e}")

    try:
        scheduler.init_app(app)
        scheduler.start()
    except SchedulerAlreadyRunningError as e:
        app.logger.info(f"Unable to start scheduler {e}")

    try:
        broker.init_app(app)
    except Exception as e:
        raise ValueError(f"Unable to start broker {e}")


def shutdown(sender, **extra):
    from app.extensions import scheduler

    try:
        scheduler.shutdown()
    # ValueError happens in case of a crash
    # I/O operation on closed fie
    except (SchedulerNotRunningError, ValueError) as e:
        # extra['app'].logger.info(f"Unable to stop scheduler {e}")
        print(f"Unable to stop scheduler {e}")


def register_blueprints(app):
    from app.blueprints.connector import connector_page
    from app.blueprints.config import config_page
    from app.blueprints.workflow import workflow_page
    from app.blueprints.heartbeat import heartbeat_page
    from app.blueprints.run import run_page

    app.register_api(connector_page)
    app.register_api(config_page)
    app.register_api(workflow_page)
    app.register_api(heartbeat_page)
    app.register_api(run_page)

    app.cli.add_command(recreate_db)


def setup_heartbeat():
    from app.core.heartbeat_service import heartbeat_service
    from app.extensions import scheduler

    scheduler.add_job(
        func=heartbeat_service,
        trigger="interval",
        seconds=scheduler.app.config["HEARTBEAT_INTERVAL"] / 2,
        args=[scheduler.app.config["HEARTBEAT_INTERVAL"]],
        id="heartbeat_service",
        replace_existing=True,
    )


@click.command("recreate-db")
@with_appcontext
def recreate_db():
    from app.extensions import elastic
    from flask import current_app
    from app.core.models import (
        Connector,
        RunConfig,
        ConnectorInstance,
        Run,
        Workflow,
        BaseDocument,
    )

    BaseDocument._index.delete(ignore=[400, 404], using=elastic.connection)

    Connector.init(using=elastic.connection)
    ConnectorInstance.init(using=elastic.connection)
    RunConfig.init(using=elastic.connection)
    Workflow.init(using=elastic.connection)
    Run.init(using=elastic.connection)

    elastic.connection.indices.refresh(index=INDEX_NAME)

    current_app.logger.info("Flushed database")
