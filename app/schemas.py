from app.models import Workflow, Connector, ConnectorRunConfig
from app.extensions import ma


class WorkflowSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        fields = ("id", "name", "root_node", "node_dependencies")
        model = Workflow
        # include_fk = True
        # include_relationships = True
        # load_instance = True


class ConnectorSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Connector

        # include_relationships = True
        # load_instance = True


class ConnectorRunConfigSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = ConnectorRunConfig
        include_fk = True
        # include_relationships = True
        # load_instance = True


connector_schema = ConnectorSchema()
connectors_schema = ConnectorSchema(many=True)
workflow_schema = WorkflowSchema()
workflows_schema = WorkflowSchema(many=True)
connector_config_schema = ConnectorRunConfigSchema()
connector_configs_schema = ConnectorRunConfigSchema(many=True)


