from app import create_app, INDEX_NAME
from app.extensions import elastic
from flask.cli import FlaskGroup

from app.core.models import (
    Connector,
    RunConfig,
    ConnectorInstance,
    Run,
    Workflow,
    BaseDocument,
)

app = create_app()
cli = FlaskGroup(create_app=create_app)


@cli.command("recreate_db")
def recreate_db():
    BaseDocument._index.delete(ignore=[400, 404], using=elastic.connection)

    Connector.init(using=elastic.connection)
    ConnectorInstance.init(using=elastic.connection)
    RunConfig.init(using=elastic.connection)
    Workflow.init(using=elastic.connection)
    Run.init(using=elastic.connection)

    elastic.connection.indices.refresh(index=INDEX_NAME)

    print("Flushed database")


if __name__ == "__main__":
    cli()
