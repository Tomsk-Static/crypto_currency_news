from flask_login import UserMixin
from swetheart import db, manager
from datetime import datetime


crypto_users = db.Table('crypto_users',
                        db.Column('user_id', db.Integer, db.ForeignKey('user.id')),
                        db.Column('crypto_id', db.Integer, db.ForeignKey('crypto.id'))
                        )


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False, unique=True)
    password = db.Column(db.String(50), nullable=False, unique=True)
    date = db.Column(db.DateTime, default=datetime.utcnow)

    my_crypto = db.relationship('Crypto', secondary=crypto_users, backref=db.backref('holders', lazy='dynamic'))

    def __repr__(self):
        return '<User {}, id: {}, my_crypto: {}>'.format(self.name, self.id, [c.crypto_name for c in self.my_crypto])



class Crypto(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    crypto_name = db.Column(db.String(10), nullable=False, unique=True)

    def __repr__(self):
        return '<Crypto {}, id: {}, holders: {}>'.format(self.crypto_name, self.id, self.holders)

@manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)