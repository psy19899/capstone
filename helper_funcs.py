from flask import request
from extensions import admin_token
from flask_jwt_extended import get_jwt_identity
from models.users import User
def get_token():
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return -1
    
    token = auth_header.split(' ')[1]

    return token

#!check if user belongs to the team
def is_TEAM_FAN(team_name):
    userid = get_jwt_identity()

    user = User.query.filter_by(id=userid).first() 
    if user and user.team == team_name:
        return True 
    return False 

def is_admin():
    token = get_token()
    if token == admin_token: 
        return True 
    return False  