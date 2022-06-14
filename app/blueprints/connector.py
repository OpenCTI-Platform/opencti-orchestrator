# from app.schemas import connector_schema, connectors_schema
import time
from datetime import datetime

from elasticsearch_dsl import Q
from elasticsearch_dsl.exceptions import ValidationException
from flask import current_app, make_response, jsonify
from flask_openapi3 import APIBlueprint, Tag
from pycti.connector.v2.libs.orchestrator_schemas import (
    ConnectorCreate,
    Connector as ConnectorSchema,
)
from pydantic import BaseModel, Field

from app.core.models import Connector, ConnectorInstance, ErrorMessage

tag = Tag(name="connector", description="Connector Management")
connector_page = APIBlueprint(
    "connector", __name__, url_prefix="/connector", abp_tags=[tag]
)


class ConnectorPath(BaseModel):
    connector_id: str = Field("connector_id", description="ID of connector instance")


@connector_page.get(
    "",
    summary="Get all Connectors",
    description="Get all existing connectors",
    responses={"200": ConnectorSchema, "404": ErrorMessage},
)
def get_all():
    results = Connector.get_all()
    results = [run.to_orm().dict() for run in results]
    return make_response(jsonify(results, 200))


@connector_page.get(
    "/<string:connector_id>",
    summary="Get Connector",
    description="Get existing Connector",
    responses={"200": ConnectorSchema, "404": ErrorMessage},
)
def get(path: ConnectorPath):
    connector = Connector.get(id=path.connector_id)
    if not connector:
        return make_response(jsonify(message="Not Found"), 404)
    else:
        return make_response(jsonify(connector.to_orm().dict()), 200)


@connector_page.post(
    "/",
    summary="Add new Connector",
    description="Add new Connector",
    # responses={"201": ConnectorSchema, "404": ErrorMessage}, # 201 schema is wrong
)
def post(body: ConnectorCreate):
    connector = Connector(**body.dict())

    # TODO use facetted search
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
        return make_response(
            jsonify(f"{{Chosen fields are not unique: {result} }}"), 400
        )

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
        return make_response(
            jsonify(
                f"More than 1 connector registered, please delete one of those ids {summary}"
            ),
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
            return make_response(jsonify(str(e)), 400)

    connector_instance = ConnectorInstance(
        last_seen=int(time.time()), connector_id=connector_id, status="available"
    )
    connector_instance_meta = connector_instance.save(return_doc_meta=True)

    config = {
        "environment": {
            "broker": {
                # TODO read broker settings dynamically
                "type": "pika",
                "user": current_app.config["RABBITMQ_USER"],
                "password": current_app.config["RABBITMQ_PASSWORD"],
                "host": current_app.config["RABBITMQ_HOSTNAME"],
                "port": current_app.config["RABBITMQ_PORT"],
            },
            "heartbeat": {
                "interval": current_app.config["HEARTBEAT_INTERVAL"],
            },
            "opencti": current_app.config["OPENCTI_URL"],
        },
        "connector_instance": connector_instance_meta["_id"],
        "connector": connector.to_orm().dict(),
    }
    return make_response(jsonify(config), 201)


@connector_page.delete(
    "/<string:connector_id>",
    summary="Delete Connector",
    description="Delete connector",
    # responses={"201": "", "404": ErrorMessage},
)
def delete(path: ConnectorPath):
    connector = Connector.get(id=path.connector_id)
    if not connector:
        return make_response(jsonify(message="Not Found"), 404)

    connector.delete()
    return make_response(jsonify(), 204)
