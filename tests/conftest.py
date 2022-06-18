from app import create_app, INDEX_NAME
import pytest


@pytest.fixture(scope="function")
def test_client():
    flask_app = create_app("config/test-config.yml")

    # Create a test client using the Flask application configured for testing
    with flask_app.test_client() as testing_client:
        # Establish an application context
        with flask_app.app_context():
            yield testing_client  # this is where the testing happens!


@pytest.fixture(scope="module")
def init_database():
    from app.core.models import (
        Connector,
        RunConfig,
        ConnectorInstance,
        Run,
        Workflow,
        BaseDocument,
    )
    from app.extensions import elastic

    flask_app = create_app("config/test-config.yml", False)

    with flask_app.app_context():
        Connector.init(using=elastic.connection)
        ConnectorInstance.init(using=elastic.connection)
        RunConfig.init(using=elastic.connection)
        Workflow.init(using=elastic.connection)
        Run.init(using=elastic.connection)

        elastic.connection.indices.refresh(index=INDEX_NAME)

        yield

        BaseDocument._index.delete(ignore=[400, 404], using=elastic.connection)
