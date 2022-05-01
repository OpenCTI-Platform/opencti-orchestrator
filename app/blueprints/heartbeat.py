from flask import Blueprint, request
from datetime import datetime

from app.extensions import elastic
from app.models import ConnectorInstance

# from app.extensions import db
from sqlalchemy.sql import func


heartbeat_page = Blueprint("heartbeat", __name__)


@heartbeat_page.route("/<string:instance_id>", methods=["PUT"])
def update(instance_id: int):
    instance = ConnectorInstance.get(id=instance_id)
    if not instance:
        return "", 404
    instance.update(last_seen=datetime.now())
    return "OK", 201


@heartbeat_page.route("/<string:instance_id>", methods=["DELETE"])
def delete(instance_id: int):
    instance = ConnectorInstance.get(id=instance_id)
    if not instance:
        return "", 404

    instance.delete()
    return "", 204


# TODO implement heartbeat service, to check current status
# https://stackoverflow.com/questions/21214270/how-to-schedule-a-function-to-run-every-hour-on-flask
