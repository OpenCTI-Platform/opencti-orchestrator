from flask_openapi3 import APIBlueprint, Tag
from pycti.connector.v2.libs.orchestrator_schemas import (
    State,
    Result,
    RunUpdate,
    Run as RunSchema,
    RunCreate,
)
from flask import jsonify, make_response
from pydantic import BaseModel, Field

from app.core.models import Run, JobStatus, ErrorMessage

tag = Tag(name="run", description="Run Management")
run_page = APIBlueprint("run", __name__, url_prefix="/run", abp_tags=[tag])


class RunPath(BaseModel):
    run_id: str = Field("run_id", description="ID of connector instance")


@run_page.get(
    "/<string:run_id>",
    summary="Get Run",
    description="Get Run",
    responses={"201": RunSchema, "400": ErrorMessage},
)
def get(path: RunPath):
    run = Run.get(id=path.run_id)
    if run:
        return make_response(jsonify(run.to_orm().dict()), 200)
    else:
        return make_response(jsonify(message="Not Found"), 404)


@run_page.put(
    "/<string:run_id>",
    summary="Update RUN",
    description="Update Run",
    responses={"201": RunSchema, "400": ErrorMessage, "404": ErrorMessage},
)
def update(path: RunPath, body: RunUpdate):
    # json_data = get_json(request)
    # command = RunUpdateSchema(**json_data)
    # print(f"context: {current_app.app_context()}")
    # if command.command == "delete":
    #     # TODO won't work, since scheduling job isn't registered with run_id
    #     scheduler.remove_job(id=run_id)
    #     current_app.logger.info("Task removed")
    if body.command == "job_status":
        run = Run.get(id=path.run_id)
        if run is None:
            return make_response(jsonify(message="Run Not Found"), 400)
        if run.status != State.running and run.result is not None:
            return make_response(
                jsonify(
                    message=f"Unable to update run due to status '{run.status}' and result '{run.result}'. "
                ),
                400,
            )

        config_id = body.parameters.get("config_id", None)
        status = body.parameters.get("status", None)
        result = body.parameters.get("result", None)

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
            return make_response(jsonify(message="Can't find config_id"), 404)

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

    return make_response(jsonify(), 200)


@run_page.delete(
    "/<string:run_id>",
    summary="Delete Run",
    description="Delete Run",
    # responses={"201": RunSchema, "404": ErrorMessage},
)
def delete(path: RunPath):
    # remove run
    # also remove scheduled job if scheduled setting
    pass
