import os
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

def init_db(app):
    db.init_app(app)
    # Import models here to allow creation
    import models
    with app.app_context():
        db.create_all()
