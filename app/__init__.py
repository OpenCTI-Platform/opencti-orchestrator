import atexit

from flask import Flask

RABBITMQ_USER = "SjIHMjmnYyRtuDf"
RABBITMQ_PASSWORD = "EVOCuAGfhOEYmmt"
RABBITMQ_URL = "rabbitmq"


def create_app(config_filename=None):
    app = Flask(__name__, instance_relative_config=True)
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:////tmp/test.db"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["SCHEDULER_API_ENABLED"] = False
    # TODO handle config load
    # app.config.from_pyfile(config_filename)
    initialize_extensions(app)
    register_blueprints(app)
    atexit.register(shutdown)
    return app


def initialize_extensions(app):
    from app.extensions import db, ma #, scheduler

    db.init_app(app)
    ma.init_app(app)
    # scheduler.init_app(app)
    # scheduler.start()

def shutdown():
    from app.extensions import scheduler
    scheduler.shutdown()

def register_blueprints(app):
    from app.blueprints.connector import connector_page
    from app.blueprints.connector_config import connector_config_page
    from app.blueprints.workflow import workflow_page
    from app.blueprints.heartbeat import heartbeat_page

    app.register_blueprint(connector_page, url_prefix='/connector')
    app.register_blueprint(connector_config_page, url_prefix='/config')
    app.register_blueprint(workflow_page, url_prefix='/workflow')
    app.register_blueprint(heartbeat_page, url_prefix='/heartbeat')
