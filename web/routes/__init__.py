from quart import Quart
# from routes.dashboard import dashboard_bp
# from routes.auth import auth_bp
from routes.instructions import instructions_bp

def register_routes(app: Quart):
    # app.register_blueprint(dashboard_bp)
    # app.register_blueprint(auth_bp)
    app.register_blueprint(instructions_bp)