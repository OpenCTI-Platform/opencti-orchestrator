import logging

from flask import Flask
from pydantic.error_wrappers import ValidationError
from apscheduler.schedulers import (
    SchedulerAlreadyRunningError,
    SchedulerNotRunningError,
)

from app.modules.config import FlaskSettings
from flask import appcontext_tearing_down


INDEX_NAME = "opencti_orchestrator"

logging.basicConfig(level=logging.INFO)

# TODO enable elasticsearch logging again when logging is set to DEBUG
elastic_logger = logging.getLogger("elasticsearch")
elastic_logger.setLevel(logging.CRITICAL)


def create_app(config_filename=None):
    app = Flask(__name__, instance_relative_config=True)
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
    from app.blueprints.connector_config import connector_config_page
    from app.blueprints.workflow import workflow_page
    from app.blueprints.heartbeat import heartbeat_page
    from app.blueprints.run import run_page

    app.register_blueprint(connector_page, url_prefix="/connector")
    app.register_blueprint(connector_config_page, url_prefix="/config")
    app.register_blueprint(workflow_page, url_prefix="/workflow")
    app.register_blueprint(heartbeat_page, url_prefix="/heartbeat")
    app.register_blueprint(run_page, url_prefix="/run")
