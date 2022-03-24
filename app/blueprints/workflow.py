import json

from flask import Blueprint, request, jsonify, url_for, g
from app.extensions import db
from app.models import Workflow, ConnectorRunConfig, ConnectorMessage, ConnectorInstance, Connector
from app.schemas import workflows_schema, workflow_schema
import pika


workflow_page = Blueprint('workflow', __name__)


@workflow_page.route('')
def get_all():
    workflows = Workflow.query.all()
    return workflows_schema.dumps(workflows)


@workflow_page.route('/<int:id>')
def get(id: int):
    workflow = Workflow.query.get_or_404(id)
    return workflow_schema.dump(workflow)


@workflow_page.route('/', methods=['POST'])
def post():
    # print(request.json)
    json_data = json.loads(request.json)

    connector_instance_id = request.json.get('connector_instance', None)
    print(connector_instance_id)
    connector_instance = ConnectorInstance.query.get_or_404(connector_instance_id)
    _send_message(connector_instance.connector.queue)
    return "", 201


@workflow_page.route('/<int:id>', methods=['DELETE'])
def delete(id):
    pass


@workflow_page.route('/run/<int:id>', methods=['GET'])
def run(workflow_id):
    pass


def _send_message(connector_queue):
    pika_credentials = pika.PlainCredentials('SjIHMjmnYyRtuDf', 'EVOCuAGfhOEYmmt')
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(
            host='rabbitmq',
            port=5672,
            credentials=pika_credentials
        )
    )
    channel = connection.channel()

    channel.queue_declare(queue=connector_queue, durable=True)
    channel.basic_publish(
        exchange='',
        routing_key=connector_queue,
        body=b"running",
        properties=pika.BasicProperties(
            delivery_mode=pika.spec.PERSISTENT_DELIVERY_MODE
        ))
    connection.close()

# @workflow_page.route('/<int:id>')
# def get(id):
#     workflow = Workflow.query.get_or_404(id)
#     return workflow_schema.dump(workflow)
#
#
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
