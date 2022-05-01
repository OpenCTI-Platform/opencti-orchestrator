from app.resources.utils import BrokerClass
from pycti.connector.v2.connectors.utils import RunContainer


class StdBroker(BrokerClass):
    def send_message(self, run_container: RunContainer):
        self.app.logger.info(f"Received RunContainer: {run_container.json()}")
