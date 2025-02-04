from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

from watchlist import db


class Movie(db.Model):  
    id = db.Column(db.Integer, primary_key=True)  
    title = db.Column(db.String(60))  
    year = db.Column(db.String(4)) 

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(20))
    username = db.Column(db.String(20))  
    password_hash = db.Column(db.String(128))  

    def set_password(self, password):
        self.password_hash = generate_password_hash(
            password,
            method='pbkdf2:sha256'  
        )
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password) 
    