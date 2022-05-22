import json
import time
import uuid
from typing import List

import pytest
from elasticsearch_dsl import Search
from pycti import ConnectorType
from pydantic.main import BaseModel

from pycti.connector.v2.libs.orchestrator_schemas import (
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


def create_connector_and_config_stix(test_client) -> (str, str, str):
    # Register Connector
    stix_worker = ConnectorCreate(
        uuid="7af04c62-5783-497b-a49b-baba88b8802d",
        name="StixWorker",
        type="STIX_IMPORT",
        queue="stix_import",
        config_schema=None,
    )
    response = test_client.post("/connector/", json=stix_worker.dict())
    stix_worker = json.loads(response.data.decode())
    print(stix_worker)
    assert response.status_code == 201, f"Error {response.data.decode()}"

    stix_worker_connector = Connector(**stix_worker["connector"])
    instance_id = stix_worker["connector_instance"]

    # Register Connector Config
    stix_worker_config = ConfigCreate(
        connector_id=stix_worker_connector.id, name="StixWorker Config", config={}
    )
    response = test_client.post("/config/", json=stix_worker_config.dict())
    assert response.status_code == 201, f"Error {response.data.decode()}"
    stix_config = Config(**json.loads(response.data.decode()))
    return stix_config.id, stix_worker_connector.id, instance_id


def create_connector_and_config_external_import(test_client) -> (str, str, str):
    class TestExternalImportRunConfig(BaseModel):
        ip: str

    # Register Connector
    external_import = ConnectorCreate(
        uuid="61464bca-a9d6-47e4-a674-d50eb5df1354",
        name="ExternalImport",
        type=ConnectorType.EXTERNAL_IMPORT.value,
        queue="external_import",
        config_schema=TestExternalImportRunConfig.schema_json(),
    )
    response = test_client.post("/connector/", json=external_import.dict())
    external_import = json.loads(response.data.decode())
    print(external_import)
    assert response.status_code == 201, f"Error {response.data.decode()}"
    instance_id = external_import["connector_instance"]
    external_import_connector = Connector(**external_import["connector"])

    # Register Connector Config
    external_import_config = ConfigCreate(
        connector_id=external_import_connector.id,
        name="EI Import",
        config=TestExternalImportRunConfig(ip="192.168.14.1"),
    )
    a = external_import_config.dict()
    print(f"sending config {a}")
    response = test_client.post("/config/", json=external_import_config.dict())
    assert response.status_code == 201, f"Error {response.data.decode()}"
    ei_config = Config(**json.loads(response.data.decode()))
    return ei_config.id, external_import_connector.id, instance_id


def create_triggered_workflow(configs: List, test_client) -> str:
    # Create Workflow
    workflow = WorkflowCreate(
        name="Test Workflow Trigered",
        jobs=configs,
        execution_type=ExecutionTypeEnum.triggered,
        execution_args="",
        token="123441",
    )
    response = test_client.post("/workflow/", json=workflow.dict())
    assert response.status_code == 201, f"Error {response.data.decode()}"
    workflow_config = Workflow(**json.loads(response.data.decode()))
    return workflow_config.id


def create_scheduled_workflow(configs: List, test_client) -> str:
    # Create Workflow
    workflow = WorkflowCreate(
        name="Test Workflow Scheduled",
        jobs=configs,
        execution_type=ExecutionTypeEnum.scheduled,
        execution_args="6",
        token="123441",
    )
    response = test_client.post("/workflow/", json=workflow.dict())
    assert response.status_code == 201, f"Error {response.data.decode()}"
    workflow_config = Workflow(**json.loads(response.data.decode()))
    return workflow_config.id


def update_status(
    test_client, config_id: str, run_id: str, status: State, result: Result = None
) -> int:
    update_schema = RunUpdate(
        command="job_status",
        parameters={"config_id": config_id, "status": status, "result": result},
    )
    response = test_client.put(f"/run/{run_id}", json=update_schema.dict())
    # print(response.data.decode())
    return response.status_code
