# from importlib.resources import Resource
# from flask_restful import reqparse, abort, Api, Resource
#
# workflows = {}
#
# class Workflow(Resource):
#     def get(self, workflow_id: int):
#         self.abort_if_workflow_doesnt_exist(workflow_id)
#         return workflows[workflow_id]
#
#     def delete(self, workflow_id):
#         self.abort_if_workflow_doesnt_exist(workflow_id)
#         del workflows[workflow_id]
#         return '', 204
#
#     def put(self, workflow_id):
#         parser = reqparse.RequestParser()
#         parser.add_argument('workflow')
#
#         args = parser.parse_args()
#         workflow = {'workflow': args['workflow']}
#         workflows[workflow_id] = workflow
#         return workflow, 201
#
#     def abort_if_workflow_doesnt_exist(self, workflow_id):
#         if workflow_id not in workflows:
#             abort(404, message=f"Workflow {workflow_id} doesn't exist")
#
#     def execute(self, workflow_id: int):
#         print('executing')
#
#
# class WorkflowList(Resource):
#     def get(self):
#         return workflows
#
#     def post(self):
#         parser = reqparse.RequestParser()
#         parser.add_argument('connector_id')
#         parser.add_argument('workflow_id')
#
#         args = parser.parse_args()
#         workflow = args['connector']
#         workflow_id = args['workflow_id']
#
#         workflows[workflow_id] = workflow
#         return workflow, 201
#
# class WorkflowExecute(Resource):
#     def get(self, workflow_id):
#         # push to RabbitMQ queue
#         return "Happy"
