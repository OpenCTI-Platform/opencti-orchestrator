from flask import Blueprint, request
from datetime import datetime
from app.models import ConnectorInstance
from app.extensions import db
from sqlalchemy.sql import func


heartbeat_page = Blueprint('heartbeat', __name__)


@heartbeat_page.route('/<int:instance_id>', methods=['PUT'])
def update(instance_id: int):
    connector_instance = ConnectorInstance.query.get_or_404(instance_id)
    connector_instance.last_seen = func.now()
    db.session.add(connector_instance)
    db.session.commit()
    return "OK", 201


@heartbeat_page.route('/<int:instance_id>', methods=['DELETE'])
def delete(instance_id: int):
    connector_instance = ConnectorInstance.query.get_or_404(instance_id)
    db.session.delete(connector_instance)
    db.session.commit()
    return "", 204


# TODO implement heartbeat service, to check current status
# https://stackoverflow.com/questions/21214270/how-to-schedule-a-function-to-run-every-hour-on-flask