import logging
from flask_openapi3 import Info, OpenAPI
from pydantic.error_wrappers import ValidationError
from apscheduler.schedulers import (
    SchedulerAlreadyRunningError,
    SchedulerNotRunningError,
)
from app.modules.config import FlaskSettings


INDEX_NAME = "opencti_orchestrator"

logging.basicConfig(level=logging.INFO)

# TODO enable elasticsearch logging again when logging is set to DEBUG
elastic_logger = logging.getLogger("elasticsearch")
elastic_logger.setLevel(logging.CRITICAL)


def create_app(config_filename=None):
    # app = Flask(__name__, instance_relative_config=True)
    info = Info(
        title="OpenCTI Orchestrator", version="1.0.0"
    )  # TODO get this version from setup.py
    app = OpenAPI(__name__, info=info)
    try:
        app.config.from_object(FlaskSettings())
    except ValidationError as e:
        app.logger.error(e)
        return None
        # better handling than None

    initialize_extensions(app)
    register_blueprints(app)
    # appcontext_tearing_down.connect(shutdown)

    return app


def initialize_extensions(app):
    from app.extensions import elastic, scheduler, broker

    elastic.init_app(app)

    try:
        scheduler.init_app(app)
        scheduler.start()
    except SchedulerAlreadyRunningError as e:
        app.logger.info(f"Unable to start scheduler {e}")

    broker.init_app(app)


def shutdown(sender, **extra):
    from app.extensions import scheduler
    from flask import current_app

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
