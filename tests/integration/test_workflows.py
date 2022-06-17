import json
import time
from pycti.connector.new.libs.orchestrator_schemas import (
    RunCreate,
    Run,
    State,
    Result,
)
from tests.utils.connector_creators import (
    create_connector_and_config_external_import,
    create_connector_and_config_stix,
    create_triggered_workflow,
    update_status,
)


def test_triggered_workflow(test_client, init_database):
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

    # Time for the DB to catch up
    time.sleep(2)

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

    time.sleep(2)

    response = test_client.get(f"/run/?status={State.running.value}")
    assert response.status_code == 200, f"Error {response.data.decode()}"
    data = json.loads(response.data.decode())
    assert type(data) == list
    assert len(data[0]) == 1
    run = Run(**data[0][0])

    # Set connector status to running
    response_code = update_status(
        test_client, external_import_config_id, run.id, State.running
    )
    assert response_code == 200

    # Set connector status to finished and success
    response_code = update_status(
        test_client, external_import_config_id, run.id, State.finished, Result.success
    )
    assert response_code == 200

    # Set connector status to running
    response_code = update_status(test_client, stix_config_id, run.id, State.running)
    assert response_code == 200

    # Set connector status to finished and success
    response_code = update_status(
        test_client, stix_config_id, run.id, State.finished, Result.success
    )
    assert response_code == 200

    response = test_client.get(f"/run/{run.id}")
    assert response.status_code == 200
    run = Run(**json.loads(response.data.decode()))

    assert run.status == State.finished.value
    assert run.result == Result.success.value


def test_scheduled_workflow(test_client, init_database):
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

    time.sleep(2)

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

    time.sleep(2)

    response = test_client.get(f"/run/?status={State.running.value}")
    assert response.status_code == 200, f"Error {response.data.decode()}"
    data = json.loads(response.data.decode())
    assert type(data) == list
    assert len(data[0]) == 1
    run = Run(**data[0][0])

    # Set connector status to running
    response_code = update_status(
        test_client, external_import_config_id, run.id, State.running
    )
    assert response_code == 200

    # Set connector status to finished and success
    response_code = update_status(
        test_client, external_import_config_id, run.id, State.finished, Result.success
    )
    assert response_code == 200

    # Set connector status to running
    response_code = update_status(test_client, stix_config_id, run.id, State.running)
    assert response_code == 200

    # Set connector status to finished and success
    response_code = update_status(
        test_client, stix_config_id, run.id, State.finished, Result.success
    )
    assert response_code == 200

    response = test_client.get(f"/run/{run.id}")
    assert response.status_code == 200
    run = Run(**json.loads(response.data.decode()))

    assert run.status == State.finished.value
    assert run.result == Result.success.value
