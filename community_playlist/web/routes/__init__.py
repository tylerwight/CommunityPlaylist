from quart import Quart
from community_playlist.web.routes.dashboard import dashboard_main_bp, dashboard_guild_bp, dashboard_settings_bp, dashboard_spot_bp
from community_playlist.web.routes.auth import auth_bp
from community_playlist.web.routes.instructions import instructions_bp
from community_playlist.web.routes.home import home_bp 

def register_routes(app: Quart):
    app.register_blueprint(dashboard_main_bp)
    app.register_blueprint(dashboard_guild_bp)
    app.register_blueprint(dashboard_settings_bp)
    app.register_blueprint(dashboard_spot_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(instructions_bp)
    app.register_blueprint(home_bp)