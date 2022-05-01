import json
import uuid
from enum import Enum
from typing import List, Optional

from flask import Blueprint, request, current_app
from pydantic.types import Json
from stix2 import Bundle

from pycti import ConnectorType
from pydantic.main import BaseModel
from pycti.connector.v2.connectors.utils import (
    State,
    Result,
    RunContainer,
    RunSchema,
    ExecutionTypeEnum,
    WorkflowSchema,
)


from app.core.workflow import launch_run_instance
from app.extensions import elastic, scheduler
from app.models import Workflow
from elasticsearch_dsl.exceptions import ValidationException

from app.resources.utils import get_json

workflow_page = Blueprint("workflow", __name__)


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


# @workflow_page.route('')
# def get_all():
#     workflows = {} # Workflow.query.all()
#     # TODO implement
#     return workflows, 200
#
#


@workflow_page.route("/<string:workflow_id>")
def get(workflow_id: str):
    workflow = Workflow.get(id=workflow_id)
    if not workflow:
        return "", 404
    else:
        return workflow.to_dict(include_meta=True), 200


@workflow_page.route("/", methods=["POST"])
def post():
    # json_data = request.get_json(force=True)
    json_data = get_json(request)
    # mapper = {
    #     ConnectorType.EXTERNAL_IMPORT: Job,
    #     ConnectorType.INTERNAL_IMPORT_FILE: InternalImportJob,
    #     ConnectorType.INTERNAL_ENRICHMENT: InternalEnrichmentJob,
    #     ConnectorType.INTERNAL_EXPORT_FILE: InternalExportJob,
    #     ConnectorType.STREAM: Job,
    #     "STIX_IMPORTER": StixImportJob,
    # }
    # TODO check execution type

    workflow = Workflow(**json_data)
    try:
        workflow_meta = workflow.save(return_doc_meta=True)
    except ValidationException as e:
        return str(e), 400

    return workflow.to_dict(include_meta=True), 201


@workflow_page.route("/<string:workflow_id>", methods=["DELETE"])
def delete(workflow_id: str):
    pass


@workflow_page.route("/<string:workflow_id>/run", methods=["POST"])
def run(workflow_id: str):
    json_data = get_json(request)
    # TODO this is a stupid workaround
    # json_data["parameters"] = str(json_data["parameters"])

    run_schema = RunSchema(**json_data)
    workflow = Workflow.get(id=workflow_id)
    if workflow is None:
        return "Workflow not found", 400

    # Create run instance
    if workflow.execution_type == ExecutionTypeEnum.triggered.value:
        launch_run_instance(run_schema, workflow)
    elif workflow.execution_type == ExecutionTypeEnum.scheduled.value:
        run_id = str(
            uuid.uuid4().hex
        )  # TODO maybe find some other way Workflow_<counter>?
        scheduler.add_job(
            func=launch_run_instance,
            trigger="interval",
            seconds=6,
            args=[run_schema, workflow],
            id=run_id,
        )
    else:
        return "Fail, unsupported execution type", 400

    return "Running", 201


# @workflow_page.route("/run/<int:workflow_id>", methods=["GET"])
# def run(workflow_id):
#     #     _send_message(connector_instance.connector.queue)
#     pass

# config_id = json_data["config_id"]
# config = ConnectorRunConfig.get(id=config_id, using=elastic)
# connector = Connector.get(id=config.connector_id, using=elastic)
# step = mapper.get(connector.type)
# workflow = Workflow(
#     name="My workflow?",
#     applicant_id="???",  # where do I get it from?
#     worksteps=[
#         step(config_id=json_data["config_id"], **json_data),
#         StixImportJob(),
#     ],
# )
#
# if current_app.config["BROKER"] == "STDOUT":
#     broker = _send_stdout_message
# elif current_app.config["BROKER"] == "PIKA":
#     broker = _send_pika_message
# else:
#     return "unknown broker", 400
#
# broker(workflow)

# result = Connector. \
#     search(using=elastic.connection). \
#     filter('term', uuid=json_data['uuid']). \
#     execute()
# TODO check if name is unique and if connector_id exists
# if len(result) > 0:
#     return f"{{'uuid': 'value \"{json_data['uuid']}\" already exists}}", 400

# try:
#     workflow_meta = workflow.save(using=elastic.connection, return_doc_meta=True)
# except ValidationException as e:
#     return str(e), 400


# @workflow_page.route('/', methods=['POST'])
# def new_workflow():
#     # Parse
#     # {
#     #   1: [
#     #           {connector_id: <id>, arguments: []},
#     #           {connector_id: <id>, arguments: []},
#     #   2: []}
#
#     workflow = Workflow(
#         name=request.json['name'],
#         connector_id=request.json['connector_id']
#         )
#     db.session.add(workflow)
#     db.session.commit()
#     return workflow_schema.dump(workflow), 201
#
# @workflow_page.route('/run/<int:id>')
# def run(id):
#     workflow = Workflow.query.get_or_404(id)
#     print(Workflow.query.all())
#     print(Connector.query.with_parent(workflow).all())
#     query = Workflow.query.options(joinedload('connector'))
#     for category in query:
#         print(category)
#     print(workflow)# TODO run send message to rabbitmq
#     return workflow_schema.dump(workflow)
#
# def prepare_message(id):
#     result = {}
#     workflow = Workflow.query.get_or_404(id)
#
#
#
#

# @workflow_page.route('/', methods=['POST'])
# def post():
#     errors = workflow_schema.validate(request.json)
#     if errors:
#         return errors, 400
#
#     # Verify that all workflow configs exist
#     for node_start, node_children in request.json.get('node_dependencies', {}).items():
#         nodes = [node_start]
#         nodes += node_children
#         for node in nodes:
#             if not _config_exists(node):
#                 return "{{\"node_dependencies\":[\"'{}' config does not exist\"]}}".format(node), 400
#
#     workflow = Workflow(**request.json)
#     db.session.add(workflow)
#     db.session.commit()
#     return workflow_schema.dump(workflow), 201
#     # TODO verify that graph is acyclic
#     # for node in request.json.get('nodes', {}).items():
#
#
# def _config_exists(config_name: str) -> bool:
#     config = ConnectorConfig.query.filter_by(name=config_name).first()
#     return config is not None
