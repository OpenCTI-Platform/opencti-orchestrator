import json
import uuid
from typing import Dict

import pika
from flask import Blueprint, request, current_app
from pydantic.main import BaseModel
from stix2 import Bundle
from pycti.connector.v2.connectors.utils import (
    State,
    Result,
    RunContainer,
    RunSchema,
    RunUpdateSchema,
)


from app.blueprints.workflow import ExecutionTypeEnum
from app.extensions import elastic, scheduler
from app.models import Run, Workflow, ConnectorRunConfig, Connector, JobStatus
from app.resources.utils import get_json

run_page = Blueprint("run", __name__)


@run_page.route("/<string:run_id>")
def get(run_id: str):
    run = Run.get(id=run_id)
    if run:
        return run.to_dict(), 200
    else:
        return "None", 404


@run_page.route("/<string:run_id>", methods=["PUT"])
def update(run_id: str):
    json_data = get_json(request)
    command = RunUpdateSchema(**json_data)
    # print(f"context: {current_app.app_context()}")
    # if command.command == "delete":
    #     # TODO won't work, since scheduling job isn't registered with run_id
    #     scheduler.remove_job(id=run_id)
    #     current_app.logger.info("Task removed")
    if command.command == "job_status":
        run = Run.get(id=run_id)
        if run is None:
            return "Run doesn't exist", 400
        if run.status != State.running and run.result is not None:
            return (
                f"Unable to update run due to status '{run.status}' and result '{run.result}'. ",
                400,
            )

        config_id = command.parameters.get("config_id", None)
        status = command.parameters.get("status", None)
        result = command.parameters.get("result", None)

        config_status = None
        config_index = 0
        finished = []
        statuses = run.job_status
        for count, run_status in enumerate(statuses):
            status_id = run_status.id
            if status_id == config_id:
                config_index = count
                config_status = run_status

        if config_status is None:
            return "Can't find config_id", 400

        new_config_status = JobStatus(
            id=config_id,
            status=status,
            result=result,
        )
        statuses[config_index] = new_config_status

        for status in statuses:
            finished.append(status.result is None)

        run.update(job_status=statuses)

        # Then there are no more unfinished jobs
        if result == Result.fail:
            run.update(status=State.finished, result=Result.fail)
        elif True not in finished:
            run.update(status=State.finished, result=Result.success)

        run.save()

    return "", 200


@run_page.route("/<string:run_id>", methods=["DELETE"])
def delete(run_id: str):
    # remove run
    # also remove scheduled job if scheduled setting
    pass
