from typing import Optional, List
from app.core.brokers import pika_broker, std_broker
from flask import _app_ctx_stack

from app.core.utils import BrokerClass

brokers = {
    "RABBITMQ": pika_broker.PikaBroker,
    "STDOUT": std_broker.StdBroker,
}
BROKER_TYPES = tuple(brokers.keys())


class BrokerHandler(object):
    def __init__(self, app=None, **kwargs) -> None:
        self.app = app
        if app is not None:
            self.init_app(app, **kwargs)

    def init_app(self, app, **kwargs) -> None:
        if self.app is None:
            self.app = app

        self.args = kwargs

        app.teardown_appcontext(self.teardown)

    def connect(self, kwargs) -> BrokerClass:
        broker_value = self.app.config.get("BROKER", "RABBITMQ")

        broker_class = brokers.get(broker_value.upper(), None)
        if broker_class is None:
            raise ValueError(f"{broker_value} is not a valid broker")

        broker = broker_class(self.app, kwargs)
        return broker

    @property
    def broker(self) -> BrokerClass:
        ctx = _app_ctx_stack.top
        if ctx is not None:
            if not hasattr(ctx, "broker"):
                ctx.broker = self.connect(self.args)
            return ctx.broker

    def teardown(self, exception) -> None:
        ctx = _app_ctx_stack.top
        if hasattr(ctx, "broker"):
            ctx.broker.close()
