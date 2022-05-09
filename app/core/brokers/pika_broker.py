import pika as pika

from pycti.connector.v2.libs.orchestrator_schemas import RunContainer
from app.core.utils import BrokerClass


class PikaBroker(BrokerClass):
    def send_message(self, run_container: RunContainer):

        with self.app.app_context():
            # TODO
            # get first ID and queue
            # start sending stuff there
            pika_credentials = pika.PlainCredentials(
                self.app.config["RABBITMQ_USER"], self.app.config["RABBITMQ_PASSWORD"]
            )
            connection = pika.BlockingConnection(
                pika.ConnectionParameters(
                    host=self.app.config["RABBITMQ_HOST"],
                    port=5672,
                    credentials=pika_credentials,
                )
            )
            channel = connection.channel()

            job = run_container.jobs[0]

            channel.queue_declare(queue=job.queue, durable=True)
            channel.basic_publish(
                exchange="",
                routing_key=job.queue,
                body=b"running",
                properties=pika.BasicProperties(
                    delivery_mode=pika.spec.PERSISTENT_DELIVERY_MODE
                ),
            )
            connection.close()
