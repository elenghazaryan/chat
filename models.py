from extensions import db, argon2
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin


class CRUDMixin(object):
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer, primary_key=True)

    @classmethod
    def create(cls, **kwargs):
        instance = cls(**kwargs)
        return instance.save()

    def update(self, commit=True, **kwargs):
        for attr, value in kwargs.items():
            setattr(self, attr, value)
        return commit and self.save() or self

    def save(self, commit=True):
        db.session.add(self)
        if commit:
            db.session.commit()
        return self

    def delete(self, commit=True):
        db.session.delete(self)
        return commit and db.session.commit()


class User(CRUDMixin, UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    password_hash = db.Column(db.String(128), default=None)

    messages = db.relationship('Message', backref='user', lazy=True)

    def set_password(self, password):
        self.password_hash = argon2.generate_password_hash(password)

    def check_password(self, password):
        return argon2.check_password_hash(self.password_hash, password)

    def __init__(self, username, password_hash=None):
        self.username = username
        self.password_hash = password_hash

    def __repr__(self):
        return '<User {}>'.format(self.username)

    @classmethod
    def get_by_username(cls, username):
        return cls.query.filter_by(username=username).first()

    def get_unread_messages(self):
        return [message for message in self.messages
                if not message.is_delivered and message.is_to_user(self.username)]

    def is_authenticated(self):
        return True

    def is_active(self):
        return True

    def is_anonymous(self):
        return False

    def get_id(self):
        return self.username


class Message(CRUDMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    message = db.Column(db.Text())
    from_who = db.Column(db.String(128))
    to_who = db.Column(db.String(128))
    is_delivered = db.Column(db.Boolean, default=False)

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    def __init__(self, message, from_who, to_who):
        self.message = message
        self.from_who = from_who
        self.to_who = to_who

    def __repr__(self):
        return 'User {} send a message to {}'.format(self.from_who, self.to_who)

    def set_delivered(self, commit=True):
        self.is_delivered = True
        self.save(commit)

    def serialize(self):
        return {
            "message": self.message,
            "from": self.from_who
        }

    def is_from_user(self, username):
        return self.from_who == username

    def is_to_user(self, username):
        return self.to_who == username

    @classmethod
    def set_messages_delivered(cls, messages):
        for m in messages:
            m.set_delivered(commit=False)
        db.session.commit()


class AnonymousUser:
    is_authenticated = False
    is_active = False
    is_anonymous = True

    def get_id(self):
        return None