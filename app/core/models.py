import json

from elasticsearch_dsl import Document, Date, Keyword, Object, InnerDoc, Nested
from pycti import ConnectorType
from pycti.connector.v2.libs.orchestrator_schemas import (
    State,
    RunContainer,
    RunCreate,
    Job,
    Connector as ConnectorSchema,
    Config as ConfigSchema,
    Workflow as WorkflowSchema,
    Run as RunSchema,
)
from pydantic import BaseModel

from app import INDEX_NAME
from app.extensions import elastic
from app.modules.elasticsearch import ChoicesKeyword

connectorUniqueSchema = ["uuid", "name", "queue"]


class ErrorMessage(BaseModel):
    message: str


class BaseDocument(Document):
    orm_class = None

    def to_dict(self, include_meta=False, skip_empty=True):
        d = super(Document, self).to_dict(skip_empty=skip_empty)
        if not include_meta:
            return d

        d["id"] = self.meta["id"]
        return d

    @classmethod
    def get(cls, **kwargs):
        return super(BaseDocument, cls).get(
            **kwargs, using=elastic.connection, ignore=404
        )

    @classmethod
    def search(cls, **kwargs):
        return super(BaseDocument, cls).search(using=elastic.connection, **kwargs)

    def save(self, **kwargs):
        return super(BaseDocument, self).save(**kwargs, using=elastic.connection)

    def update(self, **kwargs):
        return super(BaseDocument, self).update(**kwargs, using=elastic.connection)

    def delete(self, using=None, index=None, **kwargs):
        return super(BaseDocument, self).delete(**kwargs, using=elastic.connection)

    class Index:
        name = INDEX_NAME


class Connector(BaseDocument):
    uuid = Keyword(required=True)
    name = Keyword(required=True)
    queue = Keyword(required=True)
    type = ChoicesKeyword(
        required=True, choices=[e.value for e in ConnectorType] + ["STIX_IMPORT"]
    )

    def to_orm(self):
        return ConnectorSchema(**self.to_dict(include_meta=True))


class ConnectorInstance(BaseDocument):
    last_seen = Date(required=True)
    # status = db.Column(db.Enum?, nullable=False)
    connector_id = Keyword(required=True)


connectorRunConfigUniqueSchema = ["name"]


class RunConfig(BaseDocument):
    name = Keyword(required=True)  # TODO make secondary key or something
    config = Object(enabled=False)
    # Single corresponding Connector
    connector_id = Keyword(required=True)

    def to_orm(self):
        return ConfigSchema(**self.to_dict(include_meta=True))


class JobStatus(InnerDoc):
    # is ID really needed to be defined?
    id = Keyword(required=True)
    status = Keyword(required=True)
    result = Keyword(required=False)


class Run(BaseDocument):
    workflow_id = Keyword(required=True)
    # OpenCTI attributes
    work_id = Keyword(required=True)
    applicant_id = Keyword(required=True)
    # Statuses
    status = Keyword(required=True)
    result = Keyword(required=False)
    job_status = Nested(JobStatus, enabled=False, required=True)
    parameters = Object(required=False)

    def create_run_container(self) -> RunContainer:
        workflow = Workflow.get(id=self.workflow_id)
        job_list = []
        for config_id in workflow.jobs:
            connector_config = RunConfig.get(id=config_id)
            connector = Connector.get(id=connector_config.connector_id)
            queue = connector.queue
            job = Job(config_id=config_id, queue=queue)
            job_list.append(job)

        # parameters = self.parameters.to_dict()
        run_container = RunContainer(
            token=workflow.token,
            bundle=None,
            jobs=job_list,
            parameters=json.dumps(self.parameters),
            work_id=self.work_id,
            run_id=self.meta["id"],
            applicant_id=self.applicant_id,
        )
        return run_container

    def to_orm(self):
        return RunSchema(**self.to_dict(include_meta=True))


class Workflow(BaseDocument):
    # name = Keyword(required=True) # TODO make unique
    # config_id = Keyword(required=True)
    name = Keyword(required=True)  # TODO make secondary key or something
    jobs = Keyword(required=True, multi=True)
    token = Keyword(required=True)
    execution_type = Keyword(required=True)
    execution_args = Keyword(required=False)

    def create_run_instance(self, run_schema: RunCreate) -> Run:
        # TODO this won't work, because meta['id'] of the Run doesn't
        # exist yet
        job_status = []
        for config_id in self.jobs:
            job_status.append(
                JobStatus(id=config_id, status=State.pending, result=None)
            )

        run = Run(
            workflow_id=self.meta["id"],
            work_id=run_schema.work_id,
            applicant_id=run_schema.applicant_id,
            parameters=run_schema.parameters,
            status=State.pending,
            result=None,
            job_status=job_status,
        )
        run.save()

        return run

    def to_orm(self):
        return WorkflowSchema(**self.to_dict(include_meta=True))


# class Workflow(db.Model):
#     id = db.Column(db.Integer, primary_key=True)
#     name = db.Column(db.String(255), nullable=False)
#     # TODO refernce to config
#     root_node = db.Column(db.String(255), nullable=False)
#     node_dependencies = db.Column(db.JSON, nullable=False)
#     schedule = db.Column(db.String(100))
#     status = db.Column(db.String(50))
#
#     # Single Corresponding ConnectorConfig
#     config_id = db.Column(db.Integer, db.ForeignKey('connector_run_config.id'), nullable=False)
#     config = db.relationship("ConnectorRunConfig")
#
#     # Single Root WorkflowNode
#     # node_id = db.Column(db.Integer, db.ForeignKey('workflow_node.id'))
#     # node = db.relationship("WorkflowNode", back_populates="workflow")
#
#
# class ConnectorMessage(BaseModel):
#     # {
#     #   workflow : {
#     #     id: ...,
#     #     node_dependencies: {
#     #       "config-1": ["config-2"],
#     #       "config-2": ["config-3"],
#     #     },
#     #   },
#     #   "config-1": {
#     #     "queue": ...,
#     #     "config": {},
#     #   },
#     #   ... # for all configs
#     #   opencti: {
#     #     "url": ...,
#     #     "token": ..., # or more granular???
#     #   }
#     node_dependencies: dict
#     configs: list[dict]
#     system_configs: dict

# class WorkflowNode(db.Model):
#
#     id = db.Column(db.Integer, primary_key=True)
#     data = db.Column(db.String(50))
#
#     # Many WorkflowNode Children
#     parent_id = db.Column(db.Integer, db.ForeignKey('workflow_node.id'))
#     children = db.relationship(
#         "WorkflowNode",
#         backref=db.backref('parent', remote_side=[id])
#     )
#
#     # Single Corresponding Workflow
#     workflow = db.relationship("Workflow", back_populates="node", uselist=False)
#
#     # # Single Corresponding ConnectorConfig
#     config_id = db.Column(db.Integer, db.ForeignKey('connector_config.id'), nullable=False)
#     config = db.relationship("ConnectorConfig")
