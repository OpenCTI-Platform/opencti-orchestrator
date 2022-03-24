import json

from flask import Blueprint, request, jsonify, url_for, g
from app.models import ConnectorRunConfig
from app.extensions import db
from app.schemas import connector_configs_schema, connector_config_schema
from sqlalchemy.exc import IntegrityError

connector_config_page = Blueprint('connector_config', __name__)


@connector_config_page.route('')
def get_all():
    configs = ConnectorRunConfig.query.all()
    return connector_configs_schema.dumps(configs)


@connector_config_page.route('/<int:id>')
def get(config_id: int):
    config = ConnectorRunConfig.query.get_or_404(config_id)
    return connector_config_schema.dump(config)


@connector_config_page.route('/', methods=['POST'])
def post():
    json_data = json.loads(request.json)
    result = connector_config_schema.validate(json_data)
    if result:
        return result, 400

    existing_config = ConnectorRunConfig.query.filter_by(
        name=json_data["name"]
    ).first()
    if not existing_config:
        try:
            config = ConnectorRunConfig(**json_data)
            db.session.add(config)
            db.session.commit()
        except IntegrityError as e:
            return str(e), 400
    else:
        print(f"{json_data['name']} config already exists")
        config = existing_config

    return connector_config_schema.dumps(config), 201


@connector_config_page.route('/<int:id>', methods=['DELETE'])
def delete(id: int):
    pass