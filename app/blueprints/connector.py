import json

from app import RABBITMQ_USER, RABBITMQ_PASSWORD, RABBITMQ_URL
from app.extensions import db, scheduler
from app.models import Connector, ConnectorInstance
from app.schemas import connector_schema, connectors_schema
from flask import Blueprint, request
from sqlalchemy.exc import IntegrityError
from sqlalchemy.sql import func
from datetime import datetime

connector_page = Blueprint('connector', __name__)


@connector_page.route('')
def get_all():
    connectors = Connector.query.all()
    return connectors_schema.dumps(connectors)


@connector_page.route('/<int:id>')
def get(connector_id: int):
    connector = Connector.query.get_or_404(connector_id)
    return connector_schema.dump(connector)


@connector_page.route('/', methods=['POST'])
def post():
    try:
        json_data = json.loads(request.json)
    except ValueError as e:
        return str(e), 400

    result = connector_schema.validate(json_data)
    if result:
        return result, 400

    existing_connector = Connector.query.filter_by(
        name=json_data["name"],
        uuid=json_data["uuid"],
        queue=json_data["queue"]
    ).first()
    if not existing_connector:
        try:
            connector = Connector(**json_data)
            db.session.add(connector)
            db.session.commit()
        except IntegrityError as e:
            return str(e), 400
    else:
        print(f"{json_data['name']} connector already exists")
        connector = existing_connector

    connector_instance = ConnectorInstance(
        last_seen=func.now(),
        connector_id=connector.id
    )
    db.session.add(connector_instance)
    db.session.commit()

    config = {
        "environment": {
            "broker": {
                "type": "pika",
                "user": RABBITMQ_USER,
                "password": RABBITMQ_PASSWORD,
                "host": RABBITMQ_URL
            }
        },
        "connector_instance": connector_instance.id,
        "connector": connector_schema.dump(connector)
    }
    return config, 201


@connector_page.route('/<int:id>', methods=['DELETE'])
def delete(connector_id: int):
    result = Connector.query.delete_or_404(id=connector_id)
    return result, 204


@connector_page.route('/schedule/', methods=['POST'])
def schedule():
    connector_id = request.json['connector']

    scheduler.add_job(func=dummy_func,
                      trigger="interval",
                      seconds=1,
                      id="test job 2",
                      name="test job 2",
                      replace_existing=True, )
    return "scheduled", 200

def dummy_func():
    dat: str = str(datetime.now())
    print(f"executing scheduled {dat}")
