# from random import randint
# from flask import current_app
# from flask_restful import reqparse, abort, Api, Resource
#
# connectors = {}
#
# post_parser = reqparse.RequestParser()
# post_parser.add_argument(
#     'connector_id', dest='connector_id',
#     required=True,
#     help='Connector ID',
# )
#
# class Connector(Resource):
#     def get(self, connector_id: int = None):
#         # args = post_parser.parse_args()
#         if connector_id:
#             print(current_app.post("asss"))
#             # connector_id = args['connector_id']
#             self.abort_if_todo_doesnt_exist(connector_id)
#             return connectors[connector_id]
#         else:
#             print(current_app.get("asss"))
#             return connectors
#
#     def delete(self, connector_id):
#         self.abort_if_todo_doesnt_exist(connector_id)
#         del connectors[connector_id]
#         return '', 204
#
#     def put(self, connector_id):
#         parser = reqparse.RequestParser()
#         parser.add_argument('connector')
#
#         args = parser.parse_args()
#         connector = {'connector': args['connector']}
#         connectors[connector_id] = connector
#         return connector, 201
#
#     def abort_if_todo_doesnt_exist(self, connector_id):
#         if connector_id not in connectors:
#             abort(404, message=f"Connector {connector_id} doesn't exist")
#
#     def post(self):
#         parser = reqparse.RequestParser()
#         parser.add_argument('connector')
#         # parser.add_argument('connector_id')
#
#         args = parser.parse_args()
#         connector = args['connector']
#         # connector_id = args['connector_id']
#         connector_id = randint(0, 1000)
#         connectors[connector_id] = connector
#         return connector, 201
#
#
