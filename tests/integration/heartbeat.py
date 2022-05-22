import json
import time

from tests.utils.connector_creators import create_connector_and_config_stix
from pycti.connector.v2.libs.orchestrator_schemas import Instance


def test_heartbeat(test_client, caplog):
    config_id, connector_id, instance_id = create_connector_and_config_stix(test_client)

    # Check if available
    response = test_client.get(f"/heartbeat/{instance_id}")
    assert response.status_code == 200
    print(response.data.decode())
    instance = Instance(**json.loads(response.data.decode()))
    assert instance.status == "available"
    # Just sleep longer than a heartbeat interval
    time.sleep(10 + 3)  # 5 = heartbeat delay and 1 to avoid race condition

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
