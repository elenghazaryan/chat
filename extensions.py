from flask_sqlalchemy import SQLAlchemy
db = SQLAlchemy()

from flask_socketio import SocketIO
socketio = SocketIO()

from flask_migrate import Migrate
migrate = Migrate()

from flask_argon2 import Argon2
argon2 = Argon2()

from flask_login import LoginManager
login_manager = LoginManager()

from flask_bootstrap import Bootstrap
bootstrap = Bootstrap()

