from werkzeug.security import generate_password_hash, check_password_hash
from extensions import db

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key = True)
    username = db.Column(db.String(20), nullable=False)
    #hashed_password = db.Column(db.String(512), nullable=True)
    team = db.Column(db.String(10), nullable=False)
    
    def __init__(self, username, team):
        self.username = username 
        self.team = team 

    def set_password(self, password):
        self.hashed_password = generate_password_hash(password) 

    def set_team(self, team):
        self.team = team 
    
    def verify_password(self, password):
        return check_password_hash(self.hashed_password, password)

    