from flask_openapi3 import APIBlueprint, Tag
from pycti.connector.v2.libs.orchestrator_schemas import (
    Config as ConfigSchema,
    ConfigCreate,
)
from pydantic import BaseModel, Field, ValidationError
from flask import make_response, jsonify
from app.core.models import RunConfig, ErrorMessage

tag = Tag(name="config", description="Configuration Management")
config_page = APIBlueprint("config", __name__, url_prefix="/config", abp_tags=[tag])


class ConfigPath(BaseModel):
    config_id: str = Field("config_id", description="ID of connector instance")


@config_page.get(
    "/",
    summary="Get all Configs",
    description="Get all Configs",
    responses={"201": ConfigSchema, "404": ErrorMessage},
)
def get_all():
    configs = {}  # ConnectorRunConfig.query.all()
    # TODO implement
    return configs, 200  # connector_configs_schema.dumps(configs)


@config_page.get(
    "/<string:config_id>",
    summary="Get Config",
    description="Get Config",
    responses={"201": ConfigSchema, "404": ErrorMessage},
)
def get(path: ConfigPath):
    config = RunConfig.get(id=path.config_id)
    if not config:
        response = make_response(jsonify(message="Not Found"), 404)
    else:
        response = make_response(jsonify(config.to_orm().dict()), 200)

    return response


@config_page.post(
    "/",
    summary="Add a new config",
    description="Add new config",
    responses={"201": ConfigSchema, "400": ErrorMessage},
)
def post(body: ConfigCreate):
    config = RunConfig(**body.dict())

    # result = Connector. \
    #     search(using=elastic.connection). \
    #     filter('term', uuid=json_data['uuid']). \
    #     execute()
    # TODO check if name is unique and if connector_id exists
    # if len(result) > 0:
    #     return f"{{'uuid': 'value \"{json_data['uuid']}\" already exists}}", 400

    try:
        connector_config_meta = config.save(return_doc_meta=True)
    # except ValidationException as e:
    #     return make_response(e, 442)
    except ValidationError as e:
        return make_response(e.json(), 422)

    return make_response(jsonify(config.to_orm().dict()), 201)


@config_page.put(
    "/<string:config_id>",
    summary="Update existing config",
    description="Update existing Run Config",
    responses={"201": ConfigSchema, "400": ErrorMessage, "404": ErrorMessage},
)
def put(path: ConfigPath, body: ConfigCreate):
    # connector_config = RunConfig(**body)

    # result = Connector. \
    #     search(using=elastic.connection). \
    #     filter('term', uuid=json_data['uuid']). \
    #     execute()
    # TODO check if name is unique and if connector_id exists
    # if len(result) > 0:
    #     return f"{{'uuid': 'value \"{json_data['uuid']}\" already exists}}", 400

    config = RunConfig.get(id=path)
    try:
        connector_config_meta = config.update(**body)
    except ValidationError as e:
        return make_response(e.json(), 422)

    return make_response(jsonify(config.to_orm().dict()), 201)


@config_page.delete(
    "/<string:config_id>",
    summary="Delete Config",
    description="Delete Run Config",
    # responses={"204": "", "404": ErrorMessage},
)
def delete(path: ConfigPath):
    config = RunConfig.get(id=path.config_id)
    if not config:
        return make_response(jsonify(message="Not Found"), 404)
    else:
        config.delete()
        return make_response(jsonify(), 204)
