import time
from datetime import datetime

# import Datetime as Datetime

from app.core.models import Connector, ConnectorInstance
from app.extensions import scheduler

THRESHOLD = 10


def heartbeat_service(interval: int):
    print("running heartbeat service")

    with scheduler.app.app_context():
        for connector in Connector.search().query().execute():
            for instance in (
                ConnectorInstance.search()
                .filter("term", connector_id=connector.meta.id)
                .query("exists", field="last_seen")
                .execute()
            ):
                print(f"Instance connector '{instance.connector_id}' instance '{instance.meta.id}'")
                if instance.last_seen > (time.time() - interval):
                    print(f"Setting to available")
                    instance.status = "available"
                else:
                    print(f"Setting to unavailable")
                    instance.status = "unavailable"

                instance.save()

    # TODO implement heartbeat service
    # check every run when each connector last contacted the scheduler
    # and disable connectors which haven't been responding in X time
