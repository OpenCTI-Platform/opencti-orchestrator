import json
import time

from tests.utils.connector_creators import create_connector_and_config_stix
from pycti.connector.new.libs.orchestrator_schemas import Instance
from app.extensions import scheduler


def test_heartbeat(test_client, init_database):
    config_id, connector_id, instance_id = create_connector_and_config_stix(test_client)

    # Check if available
    response = test_client.get(f"/heartbeat/{instance_id}")
    assert response.status_code == 200
    print(response.data.decode())
    instance = Instance(**json.loads(response.data.decode()))
    assert instance.status == "available"

    old_job_status = scheduler.get_job("heartbeat_service")
    # If Job.next_run_time doesn't exist, try the command line
    old_run_time = old_job_status.next_run_time
    change = 0
    # Wait for at least one finished job
    while change < 3:
        time.sleep(0.5)
        new_run_time = scheduler.get_job("heartbeat_service").next_run_time
        if new_run_time > old_run_time:
            change += 1
            old_run_time = new_run_time

    # Check if unavailable
    response = test_client.get(f"/heartbeat/{instance_id}")
    assert response.status_code == 200
    instance = Instance(**json.loads(response.data.decode()))
    assert instance.status == "unavailable"

    # Send heartbeat
    response = test_client.put(f"/heartbeat/{instance_id}")
    assert response.status_code == 201

    # Check if available
    response = test_client.get(f"/heartbeat/{instance_id}")
    assert response.status_code == 200
    instance = Instance(**json.loads(response.data.decode()))
    assert instance.status == "available"
