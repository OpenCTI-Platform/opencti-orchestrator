import uuid

from elasticsearch_dsl.exceptions import ValidationException
from flask_openapi3 import APIBlueprint, Tag
from pycti.connector.v2.libs.orchestrator_schemas import (
    RunCreate,
    ExecutionTypeEnum,
    WorkflowCreate,
    Workflow as WorkflowSchema,
)
from pydantic import BaseModel, Field
from flask import make_response, jsonify, current_app
from app.core.workflow import launch_run_instance, verify_running_connectors
from app.extensions import scheduler
from app.core.models import Workflow, ErrorMessage, RunConfig, ConnectorInstance

tag = Tag(name="workflow", description="Workflow Management")

workflow_page = APIBlueprint(
    "workflow", __name__, url_prefix="/workflow", abp_tags=[tag]
)


# class WorkflowSchema(BaseModel):
#     name: str
#     jobs: List[str]
#     token: str
#     execution_type: ExecutionTypeEnum
#     execution_args: Optional[str]
# execution: {
#   type: "schedule/triggered"
#   schedule: "@hourly/23:11 @week/@now"
# }


class WorkflowPath(BaseModel):
    workflow_id: str = Field("workflow_id", description="ID of connector instance")


@workflow_page.get(
    "/",
    summary="Get all workflows",
    description="Get all Workflows",
    # responses={"201": HeartBeatResponse, "404": HeartBeatResponse},
)
def get_all():
    workflows = {}  # Workflow.query.all()
    # TODO implement
    return make_response(jsonify(workflows), 200)


@workflow_page.get(
    "/<string:workflow_id>",
    summary="Get existing Workflow",
    description="Get workflow",
    responses={"201": WorkflowSchema, "404": ErrorMessage},
)
def get(path: WorkflowPath):
    workflow = Workflow.get(id=path.workflow_id)
    if not workflow:
        response = make_response(jsonify(message="Not found"), 404)
    else:
        response = make_response(jsonify(workflow.to_orm().dict()), 200)

    return response


@workflow_page.post(
    "/",
    summary="Add new Workflow",
    description="Add new workflow",
    responses={"201": WorkflowSchema, "404": ErrorMessage},
)
def post(body: WorkflowCreate):
    # json_data = request.get_json(force=True)
    # json_data = get_json(request)
    # mapper = {
    #     ConnectorType.EXTERNAL_IMPORT: Job,
    #     ConnectorType.INTERNAL_IMPORT_FILE: InternalImportJob,
    #     ConnectorType.INTERNAL_ENRICHMENT: InternalEnrichmentJob,
    #     ConnectorType.INTERNAL_EXPORT_FILE: InternalExportJob,
    #     ConnectorType.STREAM: Job,
    #     "STIX_IMPORTER": StixImportJob,
    # }
    # TODO check execution type

    workflow = Workflow(**body.dict())
    try:
        workflow_meta = workflow.save(return_doc_meta=True)
    except ValidationException as e:
        return make_response(jsonify(message=str(e)), 400)

    return make_response(jsonify(workflow.to_orm().dict()), 201)


@workflow_page.put(
    "/<string:workflow_id>",
    summary="Update Workflow",
    description="Update existing workflow",
    responses={"201": WorkflowSchema, "404": ErrorMessage},
)
def update(path: WorkflowPath, body: WorkflowSchema):
    # json_data = request.get_json(force=True)
    # json_data = get_json(request)
    # mapper = {
    #     ConnectorType.EXTERNAL_IMPORT: Job,
    #     ConnectorType.INTERNAL_IMPORT_FILE: InternalImportJob,
    #     ConnectorType.INTERNAL_ENRICHMENT: InternalEnrichmentJob,
    #     ConnectorType.INTERNAL_EXPORT_FILE: InternalExportJob,
    #     ConnectorType.STREAM: Job,
    #     "STIX_IMPORTER": StixImportJob,
    # }
    # TODO check execution type

    # workflow = Workflow(**body)
    workflow = Workflow.get(id=path.workflow_id)
    try:
        workflow_meta = workflow.update(**body.dict())
    except ValidationException as e:
        return make_response(jsonify(message=str(e)), 400)

    return make_response(jsonify(workflow.orm()), 201)


@workflow_page.delete(
    "/<string:workflow_id>",
    summary="Delete workflow",
    description="Delete existing workflow",
    # responses={"201": "", "404": ErrorMessage},
)
def delete(path: WorkflowPath):
    pass


@workflow_page.post(
    "/<string:workflow_id>/run",
    summary="Execute Run",
    description="Initiate a Run based on Workflow ",
    responses={"201": ErrorMessage, "400": ErrorMessage, "404": ErrorMessage},
)
def run(path: WorkflowPath, body: RunCreate):
    workflow = Workflow.get(id=path.workflow_id)
    if workflow is None:
        return make_response(jsonify(message="Not Found"), 404)

    try:
        verify_running_connectors(workflow)
    except ValueError as e:
        return make_response(jsonify(message=str(e)), 400)

    # Create run instance
    if workflow.execution_type == ExecutionTypeEnum.triggered.value:
        run_instance = launch_run_instance(body, workflow)
        return make_response(jsonify(run_instance.to_orm().dict()), 201)
    elif workflow.execution_type == ExecutionTypeEnum.scheduled.value:
        run_id = str(
            uuid.uuid4().hex
        )  # TODO maybe find some other way Workflow_<counter>?
        scheduler.add_job(
            func=launch_run_instance,
            trigger="interval",
            seconds=int(workflow.execution_args),
            args=[body, workflow],
            id=run_id,
        )
        return make_response(
            jsonify(message=f"Scheduled for run. First job ID {run_id}"), 201
        )
    else:
        return make_response(jsonify(message="Fail, unsupported execution type"), 400)

    # return make_response(jsonify(message="Running"), 201)
