import json
import logging
import time

from tests.utils.connector_creators import create_connector_and_config_stix
from pycti.connector.v2.libs.orchestrator_schemas import Instance


def test_heartbeat(test_client, caplog):
    caplog.set_level(logging.DEBUG, logger="app")
    config_id, connector_id, instance_id = create_connector_and_config_stix(test_client)

    # Check if available
    response = test_client.get(f"/heartbeat/{instance_id}")
    assert response.status_code == 200
    print(response.data.decode())
    instance = Instance(**json.loads(response.data.decode()))
    assert instance.status == "available"
    # Sleep longer than a heartbeat interval
    time.sleep(10 + 3)  # 10 = heartbeat delay and 3 to avoid race condition

    message = None
    for record in caplog.records:
        if record.name != "app":
            continue
        if (
            "Hearbeat change" in record.message
            and instance.connector_id in record.message
            and instance.id in record.message
        ):
            message = record.message
            break

    assert message is not None, "Heartbeat wasn't updated"

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

    test_client.delete(f"/connector/{instance_id}")
    test_client.delete(f"/connector/{config_id}")
    test_client.delete(f"/connector/{connector_id}")
