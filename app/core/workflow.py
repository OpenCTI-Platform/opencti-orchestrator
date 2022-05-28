from typing import Optional

from flask import has_app_context

from app.core.heartbeat_service import AVAILABLE
from app.core.models import Workflow, Run, RunConfig, ConnectorInstance
from flask import current_app
from pycti.connector.v2.libs.orchestrator_schemas import (
    State,
    Result,
    RunContainer,
    RunCreate,
)
from app.extensions import broker


def launch_run_instance(run_schema: RunCreate, workflow: Workflow) -> Optional[Run]:
    if has_app_context():
        context = current_app
    else:
        context = broker.app
    with context.app_context():
        context.logger.info("running")
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
        running_connector = False
        config = RunConfig.get(id=config_id)
        for instance in (
            ConnectorInstance.search()
            .filter("term", connector_id=config.connector_id)
            .query("exists", field="last_seen")
            .execute()
        ):
            if instance.status == AVAILABLE:
                running_connector = True

        if not running_connector:
            raise ValueError(f"No running instance for connector {config.connector_id}")

    return True
