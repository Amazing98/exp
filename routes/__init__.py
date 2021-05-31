from flask import Flask
# from . import main
from .service import service_route
from .checkpoint import checkpoint
from .request import user_request
from .user import user

# register the main_app


def init_app(app: Flask):
    # prefix service is for CRUD a service
    app.register_blueprint(service_route,
                           url_prefix='/manage')
    app.register_blueprint(checkpoint,
                           url_prefix='/checkpoint')
    app.register_blueprint(user,
                           url_prefix='/user')
    app.register_blueprint(user_request,
                           url_prefix='/user_request')
