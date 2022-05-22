import importlib
import json
import os
import sys
from pathlib import Path
from tempfile import TemporaryDirectory

# from elasticsearch_dsl import Q
# from pycti.connector.v2.libs.orchestrator_schemas import ConnectorCreate, Connector as ConnectorSchema
from datamodel_code_generator import generate, InputFileType
from pydantic.error_wrappers import ValidationError
from pydantic.main import BaseModel

#
# def create_connector(schema: ConnectorCreate):
#     connector = Connector(**body.dict())
#
#     single_result = (
#         Connector.search()
#             .query(
#             "bool",
#             filter=[
#                 Q("term", uuid=connector.uuid)
#                 | Q("term", name=connector.name)
#                 | Q("term", queue=connector.queue)
#             ],
#         )
#             .exclude(
#             "bool",
#             filter=[
#                 Q("term", uuid=connector.uuid)
#                 & Q("term", name=connector.name)
#                 & Q("term", queue=connector.queue)
#             ],
#         )
#             .execute()
#     )
#     if len(single_result) > 0:
#         result = [f"Connector({i.uuid}, {i.name}, {i.queue})" for i in single_result]
#         return make_response(
#             jsonify(f"{{Chosen fields are not unique: {result} }}"), 400
#         )
#
#     result = (
#         Connector.search()
#             .query(
#             "bool",
#             filter=[
#                 Q("term", uuid=connector.uuid)
#                 & Q("term", name=connector.name)
#                 & Q("term", queue=connector.queue)
#             ],
#         )
#             .execute()
#     )
#


def validate_model(model_schema: dict | str, config: dict = None) -> bool | str:
    if isinstance(model_schema, dict):
        title = model_schema.get("title")
        schema = json.dumps(model_schema)
    elif isinstance(model_schema, str):
        title = json.loads(model_schema).get("title")
        schema = model_schema
    # elif isinstance(model_schema, InnerDocument)
    else:
        return False

    original_path = os.getcwd()
    with TemporaryDirectory() as temporary_directory_name:
        temporary_directory = Path(temporary_directory_name)
        output = Path(temporary_directory / f"{title}.py")

        generate(
            schema,
            input_file_type=InputFileType.JsonSchema,
            input_filename="example.json",
            output=output,
        )
        os.chdir(output.parent)
        sys.path.insert(0, "")
        _tmp = importlib.import_module(f"{title}")
        model: BaseModel = getattr(_tmp, title)

        # Reset modified settings
        os.chdir(original_path)
        sys.path.pop(0)

    if config is None:
        return True

    try:
        model.validate(config)
    except ValidationError as e:
        print(e)
        return False
    return True
