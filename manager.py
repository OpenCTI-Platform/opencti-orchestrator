from app import create_app
from app.extensions import db

# Call the application factory function to construct a Flask application
# instance using the development configuration
app = create_app('flask.cfg')
with app.app_context() as context:
    db.drop_all()
    db.create_all()
