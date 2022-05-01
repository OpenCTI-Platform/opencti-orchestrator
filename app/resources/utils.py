import json
from flask import Request
from pycti.connector.v2.connectors.utils import RunContainer


class BrokerClass(object):
    def __init__(self, app, args):
        self.app = app
        self.args = args

    def close(self):
        pass

    def send_message(self, run_container: RunContainer):
        pass


def get_json(request: Request):
    if not isinstance(request.json, dict):
        try:
            json_data = json.loads(request.json)
        except ValueError as e:
            return str(e), 400
    else:
        json_data = request.json

    return json_data
