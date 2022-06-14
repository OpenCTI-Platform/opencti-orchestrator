import json
import time
import pytest
from elasticsearch_dsl import Search
from app import INDEX_NAME
from pycti.connector.new.libs.orchestrator_schemas import (
    RunCreate,
    RunUpdate,
    Run,
    RunContainer,
    State,
    Result,
    WorkflowCreate,
    Workflow,
    ExecutionTypeEnum,
    ConnectorCreate,
    Connector,
    ConfigCreate,
    Config,
)
from app.extensions import elastic
from tests.utils.connector_creators import (
    create_connector_and_config_external_import,
    create_connector_and_config_stix,
    create_triggered_workflow,
    update_status,
    create_scheduled_workflow,
)


@pytest.fixture()
def clear_test_suite(test_client):
    s = Search(index=INDEX_NAME, using=elastic.connection).query("match_all")
    try:
        response = s.delete(refresh=True)
        response = [i for i in response]
        print(f"cleared {response}")
    except:
        pass

    # elastic.connection.indices.refresh(index=INDEX_NAME)
    # elastic.connection.refresh(index=INDEX_NAME)

    yield
    s = Search(index=INDEX_NAME, using=elastic.connection).query("match_all")
    try:
        response = s.delete(refresh=True)
        response = [i for i in response]
        print(f"cleared {response}")
    except:
        pass

    # elastic.connection.indices.refresh(index=INDEX_NAME)
    # elastic.connection.refresh(index=INDEX_NAME)


def test_triggered_workflow(test_client, caplog, clear_test_suite):
    """
    GIVEN a Flask application configured for testing
    WHEN the '/login' page is requested (GET)
    THEN check the response is valid
    """
    (
        external_import_config_id,
        external_import_connector_id,
        _,
    ) = create_connector_and_config_external_import(test_client)
    stix_config_id, stix_connector_id, _ = create_connector_and_config_stix(test_client)

    workflow_id = create_triggered_workflow(
        [stix_config_id, external_import_config_id], test_client
    )

    # Setup Workflow Run
    workflow_run = RunCreate(
        workflow_id=workflow_id,
        work_id="",
        applicant_id="",
        arguments="{}",
    )
    response = test_client.post(
        f"/workflow/{workflow_id}/run", json=workflow_run.dict()
    )
    assert response.status_code == 201, f"Error {response.data.decode()}"

    time.sleep(1)
    run_id = None
    for record in caplog.records:
        if "Received RunContainer" in record.message:
            run_container = RunContainer(
                **json.loads(record.message.split("RunContainer: ")[1])
            )
            run_id = run_container.run_id

    assert run_id is not None, "Could not find Run ID in log output"

    # Set connector status to running
    response_code = update_status(
        test_client, external_import_config_id, run_id, State.running
    )
    assert response_code == 200

    # Set connector status to finished and success
    response_code = update_status(
        test_client, external_import_config_id, run_id, State.finished, Result.success
    )
    assert response_code == 200

    # Set connector status to running
    response_code = update_status(test_client, stix_config_id, run_id, State.running)
    assert response_code == 200

    # Set connector status to finished and success
    response_code = update_status(
        test_client, stix_config_id, run_id, State.finished, Result.success
    )
    assert response_code == 200

    response = test_client.get(f"/run/{run_id}")
    assert response.status_code == 200
    run = Run(**json.loads(response.data.decode()))

    assert run.status == State.finished.value
    assert run.result == Result.success.value

    response = test_client.delete(f"/config/{external_import_config_id}")
    assert response.status_code == 204
    response = test_client.delete(f"/config/{stix_config_id}")
    assert response.status_code == 204

    response = test_client.delete(f"/connector/{external_import_connector_id}")
    assert response.status_code == 204
    response = test_client.delete(f"/connector/{stix_connector_id}")
    assert response.status_code == 204


def test_scheduled_workflow(test_client, caplog, clear_test_suite):
    """
    GIVEN a Flask application configured for testing
    WHEN the '/login' page is requested (GET)
    THEN check the response is valid
    """
    (
        external_import_config_id,
        external_import_connector_id,
        _,
    ) = create_connector_and_config_external_import(test_client)
    stix_config_id, stix_connector_id, _ = create_connector_and_config_stix(test_client)
    workflow_id = create_scheduled_workflow(
        [stix_config_id, external_import_config_id], test_client
    )

    # Setup Workflow Run
    workflow_run = RunCreate(
        workflow_id=workflow_id,
        work_id="",
        applicant_id="",
        arguments="{}",
    )
    response = test_client.post(
        f"/workflow/{workflow_id}/run", json=workflow_run.dict()
    )
    assert response.status_code == 201, f"Error {response.data.decode()}"

    time.sleep(8)
    run_id = None
    for record in caplog.records:
        if "Received RunContainer" in record.message:
            run_container = RunContainer(
                **json.loads(record.message.split("RunContainer: ")[1])
            )
            run_id = run_container.run_id

    assert run_id is not None, "Could not find Run ID in log output"

    # Set connector status to running
    response_code = update_status(
        test_client, external_import_config_id, run_id, State.running
    )
    assert response_code == 200

    # Set connector status to finished and success
    response_code = update_status(
        test_client, external_import_config_id, run_id, State.finished, Result.success
    )
    assert response_code == 200

    # Set connector status to running
    response_code = update_status(test_client, stix_config_id, run_id, State.running)
    assert response_code == 200

    # Set connector status to finished and success
    response_code = update_status(
        test_client, stix_config_id, run_id, State.finished, Result.success
    )
    assert response_code == 200

    response = test_client.get(f"/run/{run_id}")
    assert response.status_code == 200
    run = Run(**json.loads(response.data.decode()))

    assert run.status == State.finished.value
    assert run.result == Result.success.value

    response = test_client.delete(f"/config/{external_import_config_id}")
    assert response.status_code == 204
    response = test_client.delete(f"/config/{stix_config_id}")
    assert response.status_code == 204

    response = test_client.delete(f"/connector/{external_import_connector_id}")
    assert response.status_code == 204
    response = test_client.delete(f"/connector/{stix_connector_id}")
    assert response.status_code == 204
