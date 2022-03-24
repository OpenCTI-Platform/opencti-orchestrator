from app.extensions import db
from pydantic import BaseModel
from sqlalchemy.sql import func


class ConnectorInstance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    last_seen = db.Column(db.DateTime, server_default=func.now())
    # status = db.Column(db.Enum?, nullable=False)

    connector_id = db.Column(db.Integer, db.ForeignKey('connector.id'), nullable=False)
    connector = db.relationship("Connector")


class Connector(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    uuid = db.Column(db.String(255), nullable=False, unique=True)  # TODO make secondary key or something
    name = db.Column(db.String(255), nullable=False, unique=True)
    queue = db.Column(db.String(255), nullable=False, unique=True)
    type = db.Column(db.String(50), nullable=False)

    # Many ConnectorConfigs for this Connector
    configs = db.relationship('ConnectorRunConfig', lazy='dynamic', back_populates='connector')
    instances = db.relationship('ConnectorInstance', lazy='dynamic', back_populates='connector')


class ConnectorRunConfig(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False, unique=True)  # TODO make secondary key or something
    config = db.Column(db.JSON, nullable=False)

    # Single corresponding Connector
    connector_id = db.Column(db.Integer, db.ForeignKey('connector.id'), nullable=False)
    connector = db.relationship("Connector")

    # Many WorkflowNodes using this config
    # nodes = db.relationship('WorkflowNode', lazy='dynamic', back_populates='config')


class Workflow(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    # TODO refernce to config
    root_node = db.Column(db.String(255), nullable=False)
    node_dependencies = db.Column(db.JSON, nullable=False)
    schedule = db.Column(db.String(100))
    status = db.Column(db.String(50))

    # Single Corresponding ConnectorConfig
    config_id = db.Column(db.Integer, db.ForeignKey('connector_run_config.id'), nullable=False)
    config = db.relationship("ConnectorRunConfig")

    # Single Root WorkflowNode
    # node_id = db.Column(db.Integer, db.ForeignKey('workflow_node.id'))
    # node = db.relationship("WorkflowNode", back_populates="workflow")


class ConnectorMessage(BaseModel):
    # {
    #   workflow : {
    #     id: ...,
    #     node_dependencies: {
    #       "config-1": ["config-2"],
    #       "config-2": ["config-3"],
    #     },
    #   },
    #   "config-1": {
    #     "queue": ...,
    #     "config": {},
    #   },
    #   ... # for all configs
    #   opencti: {
    #     "url": ...,
    #     "token": ..., # or more granular???
    #   }
    node_dependencies: dict
    configs: list[dict]
    system_configs: dict

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
