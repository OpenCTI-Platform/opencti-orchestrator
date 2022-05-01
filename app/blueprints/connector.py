# from app.schemas import connector_schema, connectors_schema
import json
from datetime import datetime

from elasticsearch_dsl import Q
from elasticsearch_dsl.exceptions import ValidationException
from flask import Blueprint, request, current_app

from app.extensions import elastic
from app.models import Connector, ConnectorInstance
from pycti.connector.v2.connectors.utils import ConnectorIdentification
from app.resources.utils import get_json

connector_page = Blueprint("connector", __name__)


@connector_page.route("")
def get_all():
    connectors = {}  # Connector.query.all()
    # TODO implement
    # return connectors_schema.dumps(connectors)
    return connectors, 200


@connector_page.route("/<string:connector_id>")
def get(connector_id: str):
    connector = Connector.get(id=connector_id)
    if not connector:
        return "", 404
    else:
        return connector.to_dict(), 200


@connector_page.route("/", methods=["POST"])
def post():
    json_data = get_json(request)

    connector = Connector(**json_data)

    single_result = (
        Connector.search()
        .query(
            "bool",
            filter=[
                Q("term", uuid=connector.uuid)
                | Q("term", name=connector.name)
                | Q("term", queue=connector.queue)
            ],
        )
        .exclude(
            "bool",
            filter=[
                Q("term", uuid=connector.uuid)
                & Q("term", name=connector.name)
                & Q("term", queue=connector.queue)
            ],
        )
        .execute()
    )
    if len(single_result) > 0:
        result = [f"Connector({i.uuid}, {i.name}, {i.queue})" for i in single_result]
        return f"{{Chosen fields are not unique: {result} }}", 400

    result = (
        Connector.search()
        .query(
            "bool",
            filter=[
                Q("term", uuid=connector.uuid)
                & Q("term", name=connector.name)
                & Q("term", queue=connector.queue)
            ],
        )
        .execute()
    )
    if len(result) > 1:
        summary = [f"Connector({i.uuid}, {i.name}, {i.queue})" for i in result]
        return (
            f"More than 1 connector registered, please delete one of those ids {summary}",
            400,
        )
    elif len(result) == 1:
        # Using existing connector, only create new instance
        connector_id = result[0].meta["id"]
        connector = Connector.get(id=result[0].meta["id"])
    else:
        # Create new connector
        try:
            connector_info_meta = connector.save(return_doc_meta=True)
            connector_id = connector_info_meta["_id"]
        except ValidationException as e:
            return str(e), 400

    connector_instance = ConnectorInstance(
        last_seen=datetime.now(), connector_id=connector_id
    )
    connector_instance_meta = connector_instance.save(return_doc_meta=True)

    config = {
        "environment": {
            "broker": {
                "type": "pika",
                "user": current_app.config["RABBITMQ_USER"],
                "password": current_app.config["RABBITMQ_PASSWORD"],
                "host": current_app.config["RABBITMQ_HOST"],
            }
        },
        "connector_instance": connector_instance_meta["_id"],
        "connector": connector.to_dict(include_meta=True),
    }
    return config, 201


@connector_page.route("/<string:connector_id>", methods=["DELETE"])
def delete(connector_id: str):
    connector = Connector.get(id=connector_id)
    if not connector:
        return "", 404

    connector.delete()
    return "", 204


# @connector_page.route('/schedule/', methods=['POST'])
# def schedule():
#     connector_id = request.json['connector']
#
#     scheduler.add_job(func=dummy_func,
#                       trigger="interval",
#                       seconds=1,
#                       id="test job 2",
#                       name="test job 2",
#                       replace_existing=True, )
#     return "scheduled", 200
#
# def dummy_func():
#     dat: str = str(datetime.now())
#     print(f"executing scheduled {dat}")
