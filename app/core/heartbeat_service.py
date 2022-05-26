import time
from datetime import datetime

# import Datetime as Datetime

from app.core.models import Connector, ConnectorInstance
from app.extensions import scheduler

THRESHOLD = 10


def heartbeat_service(interval: int):
    with scheduler.app.app_context():
        for connector in Connector.search().query().execute():
            for instance in (
                ConnectorInstance.search()
                .filter("term", connector_id=connector.meta.id)
                .query("exists", field="last_seen")
                .execute()
            ):
                if instance.last_seen > (time.time() - interval):
                    instance.status = "available"
                else:
                    instance.status = "unavailable"

                instance.save()
