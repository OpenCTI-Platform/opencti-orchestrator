import time
from datetime import datetime
from flask import make_response, jsonify
from flask_openapi3 import APIBlueprint, Tag
from pydantic import BaseModel, Field

from app.core.models import ConnectorInstance

# from app.extensions import db

tag = Tag(name="heartbeat", description="Heartbeat Management")
heartbeat_page = APIBlueprint(
    "heartbeat", __name__, url_prefix="/heartbeat", abp_tags=[tag]
)


class HeartBeatPath(BaseModel):
    instance_id: str = Field("instance_id", description="ID of connector instance")


class HeartBeatResponse(BaseModel):
    message: str = Field("ok", description="Exception Information")


@heartbeat_page.get(
    "/<string:instance_id>",
    summary="Get instance info",
    # responses={"200": }
)
def get(path: HeartBeatPath):
    instance = ConnectorInstance.get(id=path.instance_id)
    if not instance:
        return make_response(jsonify(message="Not Found"), 404)
    else:
        return make_response(jsonify(instance.to_orm().dict()), 200)


@heartbeat_page.put(
    "/<string:instance_id>",
    summary="Update heartbeat for connector instance",
    description="Update heartbeat and set the last_seen value to datetime.now()",
    responses={"201": HeartBeatResponse, "404": HeartBeatResponse},
)
def update(path: HeartBeatPath):
    instance = ConnectorInstance.get(id=path.instance_id)
    if not instance:
        return make_response(jsonify(message="Not Found"), 404)
    instance.update(last_seen=int(time.time()), status="available")
    return make_response(jsonify(message="OK"), 201)


@heartbeat_page.delete(
    "/<string:instance_id>",
    summary="Delete connector instance",
    description="Delete connector instance at shutdown",
    responses={"204": HeartBeatResponse, "404": HeartBeatResponse},
)
def delete(path: HeartBeatPath):
    instance = ConnectorInstance.get(id=path.instance_id)
    if not instance:
        return make_response(jsonify(message="Not Found"), 404)

    instance.delete()
    return make_response(jsonify(), 204)


# TODO implement heartbeat service, to check current status
# https://stackoverflow.com/questions/21214270/how-to-schedule-a-function-to-run-every-hour-on-flask
