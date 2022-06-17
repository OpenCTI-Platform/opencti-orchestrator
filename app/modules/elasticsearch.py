from typing import List, Tuple, Union

from elasticsearch import Elasticsearch
from elasticsearch_dsl import Keyword
from elasticsearch_dsl.exceptions import ValidationException
from flask import _app_ctx_stack


class FlaskElasticsearch(object):
    def __init__(self, app=None, **kwargs) -> None:
        self.app = app
        if app is not None:
            self.init_app(app, **kwargs)

    def init_app(self, app, **kwargs) -> None:
        if self.app is None:
            self.app = app

        self.args = kwargs

        app.teardown_appcontext(self.teardown)

    def connect(self, kwargs) -> Elasticsearch:
        if isinstance(self.app.config.get("ELASTICSEARCH_URL"), str):
            hosts = [self.app.config.get("ELASTICSEARCH_URL")]
        elif isinstance(self.app.config.get("ELASTICSEARCH_HOST"), list):
            hosts = self.app.config.get("ELASTICSEARCH_HOST")
        else:
            raise ValueError("No host defined")

        # auth = (self.app.config.get("ELASTICSEARCH_HTTP_AUTH", None),)
        elastic = Elasticsearch(
            hosts=hosts,
            # http_auth=auth,
            **kwargs,
        )

        if not elastic.ping():
            raise ValueError("Elasticsearch connection failed")

        return elastic

    @property
    def connection(self) -> Elasticsearch:
        ctx = _app_ctx_stack.top
        if ctx is not None:
            if not hasattr(ctx, "elastic"):
                ctx.elastic = self.connect(self.args)
            return ctx.elastic

    def teardown(self, exception) -> None:
        ctx = _app_ctx_stack.top
        if hasattr(ctx, "elastic"):
            ctx.elastic.close()


# Copied from https://github.com/elastic/elasticsearch-dsl-py/issues/789#issue-280476670
class ChoicesKeyword(Keyword):
    def __init__(self, *args, **kwargs):
        self._choices = kwargs.pop("choices", ())
        super(ChoicesKeyword, self).__init__(*args, **kwargs)

    def clean(self, data: Union[List, Tuple]):
        data = super(ChoicesKeyword, self).clean(data)
        if self._choices:
            if isinstance(data, list):
                for choice in data:
                    self.validate_choice(choice, self._choices)
            else:
                self.validate_choice(data, self._choices)
        return data

    def validate_choice(self, choice: str, choices: tuple) -> None:
        if choices and choice not in choices:
            raise ValidationException(
                f"Choice {choice} not in allowed choices {self._choices}."
            )
