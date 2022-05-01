import json
from typing import Optional

from flask import Blueprint, request, jsonify, url_for, g
from pydantic.main import BaseModel

from app.models import ConnectorRunConfig
from app.extensions import elastic

# from app.schemas import connector_configs_schema, connector_config_schema
# from sqlalchemy.exc import IntegrityError
from pycti.connector.v2.connectors.utils import ConnectorRunConfigSchema
from elasticsearch_dsl.exceptions import ValidationException

from app.resources.utils import get_json

connector_config_page = Blueprint("connector_config", __name__)


@connector_config_page.route("")
def get_all():
    configs = {}  # ConnectorRunConfig.query.all()
    # TODO implement
    return configs, 200  # connector_configs_schema.dumps(configs)


@connector_config_page.route("/<string:config_id>")
def get(config_id: str):
    config = ConnectorRunConfig.get(id=config_id)
    if not config:
        return "", 404
    else:
        return config.to_dict(), 200


@connector_config_page.route("/", methods=["POST"])
def post():
    json_data = get_json(request)

    # print(f"Config {json_data}")
    connector_config = ConnectorRunConfig(**json_data)

    # result = Connector. \
    #     search(using=elastic.connection). \
    #     filter('term', uuid=json_data['uuid']). \
    #     execute()
    # TODO check if name is unique and if connector_id exists
    # if len(result) > 0:
    #     return f"{{'uuid': 'value \"{json_data['uuid']}\" already exists}}", 400

    try:
        connector_config_meta = connector_config.save(return_doc_meta=True)
    except ValidationException as e:
        return str(e), 400

    return connector_config.to_dict(include_meta=True), 201


@connector_config_page.route("/<string:config_id>", methods=["DELETE"])
def delete(config_id: str):
    connector_config = ConnectorRunConfig.get(id=config_id)
    if not connector_config:
        return "", 404

    connector_config.delete()
    return "", 204
