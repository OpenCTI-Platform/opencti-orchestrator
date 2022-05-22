from flask import has_app_context
from app.core.models import Workflow, Run
from flask import current_app
from pycti.connector.v2.libs.orchestrator_schemas import (
    State,
    Result,
    RunContainer,
    RunCreate,
)
from app.extensions import broker


def launch_run_instance(run_schema: RunCreate, workflow: Workflow) -> Run:
    if has_app_context():
        context = current_app
    else:
        context = broker.app
    with context.app_context():
        context.logger.info("running")
        run = workflow.create_run_instance(run_schema)
        run_container = run.create_run_container()
        broker.broker.send_message(run_container)
        run.update(status=State.running)
        return run
