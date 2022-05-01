import json
import logging

import pika as pika
from flask import has_app_context
from app.extensions import elastic, scheduler
from app.models import Workflow, Run, ConnectorRunConfig, Connector
from flask import current_app
from pycti.connector.v2.connectors.utils import State, Result, RunContainer, RunSchema
from app.extensions import broker


def launch_run_instance(run_schema: RunSchema, workflow: Workflow) -> Run:
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
