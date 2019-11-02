import sqlite3

from flask import Flask
import flask_login
import sqlalchemy


def configure_app(config):
    # Configure App
    app = Flask("predict")

    app.config.update(config)

    # Configure SQLAlchemy
    import predict.db
    # TODO get database location from the config
    engine = sqlalchemy.create_engine("sqlite:///db.sqlite")
    predict.db.SessionFactory.configure(bind=engine)

    # Configure LoginManager
    login_manager = flask_login.LoginManager(app)
    login_manager.login_view = "main.login"
    # TODO might want to get this key from a config file...
    app.config["SECRET_KEY"] = "secret_xxx"

    import predict.auth
    login_manager.user_loader(predict.auth.load_user)

    # Configure Data Models
    import predict.models
    predict.models.Model.metadata.create_all(engine)

    # Configure Views
    import predict.views
    app.register_blueprint(predict.views.blueprint)

    return app
