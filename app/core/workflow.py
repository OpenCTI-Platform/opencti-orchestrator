from typing import Optional

from flask import has_app_context

from app.core.heartbeat_service import AVAILABLE
from app.core.models import Workflow, Run, RunConfig, ConnectorInstance
from flask import current_app
from pycti.connector.new.libs.orchestrator_schemas import (
    State,
    RunCreate,
)
from app.extensions import broker


def launch_run_instance(run_schema: RunCreate, workflow: Workflow) -> Optional[Run]:
    if has_app_context():
        context = current_app
    else:
        context = broker.app
    with context.app_context():
        try:
            verify_running_connectors(workflow)
        except ValueError as e:
            context.logger.error(e)
            return None
        run = workflow.create_run_instance(run_schema)
        run_container = run.create_run_container()
        broker.broker.send_message(run_container)
        run.update(status=State.running)
        return run


def verify_running_connectors(workflow: Workflow) -> bool:
    for config_id in workflow.jobs:
        config: RunConfig = RunConfig.get(id=config_id)
        result = ConnectorInstance.get_all(
            filters=[{"status": AVAILABLE}, {"connector_id": config.connector_id}]
        )

        if len(result) == 0:
            raise ValueError(f"No running instance for connector {config.connector_id}")

    return True
