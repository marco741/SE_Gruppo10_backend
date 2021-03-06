from flask_restful import Api
from blacklist import BLACKLIST
import jwt_utils
from resources.user import User, UserList, UserCreate, UserLogin, UserLogout, UserChangePassword
from resources.maintenance_activity import MaintenanceActivity, MaintenanceActivityCreate, MaintenanceActivityList, MaintenanceActivityAssign
from resources.maintainer_availability import MaintainerWeeklyAvailabilityList, MaintainerDailyAvailability
from flask_seeder import FlaskSeeder


def create_app(config_class="config.Config"):
    from flask import Flask
    app = Flask(__name__)
    app.config.from_object(config_class)
    jwt_utils.bind_jwt_messages(app)
    api = Api(app)

    api.add_resource(User, "/user/<string:username>")
    api.add_resource(UserCreate, "/user")
    api.add_resource(UserList, "/users")
    api.add_resource(UserLogin, "/login")
    api.add_resource(UserLogout, "/logout")
    api.add_resource(UserChangePassword, "/change_password")
    api.add_resource(MaintenanceActivity, "/activity/<int:id>")
    api.add_resource(MaintenanceActivityCreate, "/activity")
    api.add_resource(MaintenanceActivityList, "/activities")
    api.add_resource(MaintainerWeeklyAvailabilityList,
                     "/maintainer/<int:activity_id>/availabilities")
    api.add_resource(MaintainerDailyAvailability,
                     "/maintainer/<string:username>/availability")
    api.add_resource(MaintenanceActivityAssign,
                     "/activity/<int:id>/assign")

    from db import db
    db.init_app(app)
    seeder = FlaskSeeder()
    seeder.init_app(app, db)
    return app


if __name__ == "__main__":
    app = create_app('config.Config')

    from db import db

    @app.before_first_request
    def create_tables():
        db.create_all()

    app.run()
