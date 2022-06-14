import time
from app.core.models import Connector, ConnectorInstance
from app.extensions import scheduler

THRESHOLD = 10
AVAILABLE = "available"
UNAVAILABLE = "unavailable"


def heartbeat_service(interval: int):
    with scheduler.app.app_context():
        scheduler.app.logger.debug("Heartbeat running")

        for connector in Connector.search().query("exists", field="uuid").execute():
            scheduler.app.logger.debug(
                f"Running connector {connector.name} ({connector.meta.id})"
            )

            results = ConnectorInstance.get_all(
                filters=[{"connector_id": connector.meta.id}]
            )

            for instance in results:
                scheduler.app.logger.debug(
                    f"Instance {instance.meta.id} {instance.status}"
                )
                if instance.last_seen > (time.time() - interval):
                    status = AVAILABLE
                else:
                    status = UNAVAILABLE

                if instance.status != status:
                    scheduler.app.logger.info(
                        f"Hearbeat change: {connector.name} ({connector.meta.id} instance {instance.meta.id} to {status}"
                    )
                    instance.update(status=status)
