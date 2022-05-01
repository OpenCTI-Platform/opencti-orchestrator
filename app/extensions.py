from flask_apscheduler import APScheduler
from app.modules.elasticsearch import FlaskElasticsearch
from app.modules.broker import BrokerHandler

scheduler = APScheduler()
elastic = FlaskElasticsearch()
broker = BrokerHandler()
