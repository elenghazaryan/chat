from flask import Flask, request, render_template, flash, redirect
from flask_socketio import Namespace, emit, disconnect
from extensions import db, socketio, migrate, argon2, login_manager, bootstrap
from models import Message, User, AnonymousUser
from forms import LoginForm, RegisterForm, ChatForm
from flask_login import current_user, login_user, logout_user

host = 'localhost'
port = 5001

app = Flask(__name__, static_url_path='/static')

app.config['SECRET_KEY'] = 'secret!'
app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///chat.db"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['DEBUG'] = True

db.init_app(app)
socketio.init_app(app, async_mode='threading')
migrate.init_app(app, db)
argon2.init_app(app)
login_manager.init_app(app)
bootstrap.init_app(app)

login_manager.anonymous_user = AnonymousUser


@login_manager.user_loader
def load_user(username):
    return User.query.filter_by(username=username).first()


@app.route('/')
@app.route('/index')
def index():
    if not current_user.is_authenticated:
        return redirect('/login')
    return render_template('index.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect('/index')
    form = LoginForm(request.form)
    if form.validate_on_submit():
        user = form.get_user()
        login_user(user, remember=form.remember_me.data)
        return redirect('/index')
    return render_template('login.html', title='Sign In', form=form)


@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect('/index')
    form = RegisterForm(request.form)
    if form.validate_on_submit():
        return redirect('/login')
    return render_template('register.html', title='Register', form=form)


@app.route('/logout')
def logout():
    logout_user()
    return redirect('/login')


@app.route('/chat')
def chat():
    form = ChatForm(request.form)
    if not current_user.is_authenticated:
        return redirect('/register')
    else:
        return render_template('chat.html', title='Chat', form=form)

    # if form.validate_on_submit():
    #     return redirect('/chat')


class ChatSocksApi(Namespace):
    __user_session = dict()
    __session_user = dict()

    def set_session(self, username):
        self.__user_session[username] = request.sid
        self.__session_user[request.sid] = username

    def delete_session(self):
        username = self.__session_user.pop(request.sid, None)
        self.__user_session.pop(username, None)

    def get_username_by_sid(self, sid=None):
        if not sid:
            sid = request.sid
        return self.__session_user[sid]

    def get_sid_by_username(self, username):
        return self.__user_session.get(username)

    def on_connect(self, *args):
        username = request.headers.get('username')
        password = request.headers.get('password')
        if not username or not password:
            return False

        user = User.query.filter_by(username=username).first()
        if not user:
            user = User(username=username)
            user.set_password(password)
            user.save()

        if not user.check_password(password):
            return False

        self.set_session(username)
        print(self.__user_session)
        return True

    def on_disconnect(self, *args):
        self.delete_session()
        print(self.__user_session)
        disconnect()

    def on_message(self, data):
        username_from = self.get_username_by_sid()
        user_from = User.get_by_username(username_from)
        user_to = User.get_by_username(data["to"])
        message = Message(data["message"], data["from"], data["to"])

        user_from.messages.append(message)
        user_to.messages.append(message)
        message.save()
        user_from.save()
        user_to.save()

        to_sid = self.get_sid_by_username(data['to'])
        if to_sid:
            emit("message", data['message'], room=to_sid)
            message.set_delivered()

    def on_get_updates(self):
        username = self.get_username_by_sid()
        user = User.get_by_username(username)
        messages = user.get_unread_messages()
        if messages:
            serialized_messages = [msg.serialize() for msg in messages]
            data = {"messages": serialized_messages}
            emit("update", data, room=request.sid)
            Message.set_messages_delivered(messages)


socketio.on_namespace(ChatSocksApi('/'))
if __name__ == "__main__":
    socketio.run(app=app, host=host, port=port)
