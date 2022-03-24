from flask_apscheduler import APScheduler
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
db = SQLAlchemy()
ma = Marshmallow()
scheduler = APScheduler()
