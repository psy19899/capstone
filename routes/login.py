from flask import jsonify, request, Blueprint
from models.users import User 
from extensions import db, jwt_blocklist
from Dict import TEAM_LIST
import re 
from flask_jwt_extended import jwt_required, create_access_token, get_jwt, get_jwt_identity, unset_jwt_cookies, get_jti 

login_route = Blueprint('login', __name__)

@login_route.route("/health", methods=['GET'])
def health():
    return "hello"

@login_route.route("/api/user/token", methods=['GET'])
def token():
    username = request.args.get("username") 
    team = request.args.get("team")
    
    if username is None: 
        return jsonify({"msg": "provide username"})
    if team is None:
        return jsonify({"msg": "provide team"})

    user = User.query.filter_by(username=username).first() 
    if user is not None:
        return jsonify({"msg": "username exist"})
    
    user = User(username=username, team=team) 
    db.session.add(user) 
    db.session.commit() 

    access_token = create_access_token(identity=user.id)
    return jsonify({"msg": "user logged in", "access_token": access_token}), 200



def is_clean_password(pwd):
    if re.match(r"^(?=.*[A-Za-z])(?=.*\d)(?=.*[@$!%*#?&])[A-Za-z\d@$!%*#?&]{8,14}$", pwd):
        return True 
    return False 

def is_clean_username(username):
    if re.match(r"^[a-zA-Z0-9]{1,10}$", username):
        return True 
    return False 

@login_route.route("/api/user/login", methods=["POST"])
def login():
    if not request.is_json:
        return jsonify({"error": "true", "msg": "request not in json format"}), 400

    username = request.json.get("username")
    password = request.json.get("password") 

    #check for empty request 
    if username is None or password is None:
        return jsonify({"error": "true", "msg": "input not given"}), 400

    #check username exists 
    user = User.query.filter_by(username=username).first() 
    if user is None:
        return jsonify({"error": "true", "msg": "user not exists"}), 400

    #if exists, check password 
    if not user.verify_password(password):
        return jsonify({"error": "true", "msg": "incorrect password"}), 400
    
    #if password match, authenticate user 
    """
    auth the user : generate access token and return to frontend
    """

    access_token = create_access_token(identity=user.id)
    return jsonify({"msg": "user logged in", "access_token": access_token}), 200

@login_route.route("/api/user/register", methods=["POST"])
#add access control (logged user cannot access)
def register():
    if not request.is_json:
        return jsonify({"error": "true", "msg": "request not in json format"}), 400

    username = request.json.get("username")
    password = request.json.get("password")
    password_confirm = request.json.get("password_confirm")
    team = request.json.get("team")

    #check for empty request
    if username is None or password is None or password_confirm is None or team is None:
        return jsonify({"error": "true", "msg": "input not given"}), 400
    
    #check for username
    user = User.query.filter_by(username=username).first() 
    if user is not None:
        #return user exists!
        return jsonify({"error": "true", "msg": "username exists"}), 400
    
    #check username
    if not is_clean_username(username):
        return jsonify({"error": "true", "msg": "username not clean"}), 400

    #check password and password==password_confirm
    if password != password_confirm: 
        #return password not equal 
        return jsonify({"error": "true", "msg": "password not equal"}), 400

    if not is_clean_password(password):
        #return password not secure
        return jsonify({"error": "true", "msg": "not secure password"}), 400

    #check team 
    if team not in TEAM_LIST:
        return jsonify({"error": "true", "msg": 'given team not found'}) , 400

    #create user and save to db
    user = User(username=username, team=team)
    user.set_password(password) 
    db.session.add(user)
    db.session.commit()
    return jsonify({'msg': "user created"}), 200

@login_route.route("/api/user/logout", methods=["GET"])
@jwt_required()
def logout():
    jti = get_jwt()['jti']
    jwt_blocklist.add(jti)
    return jsonify({"msg": "user logout"}), 200


@login_route.route("/api/user/password", methods=["UPDATE"])
@jwt_required() #requires login
def update_pwd():
    if not request.is_json:
        return jsonify({"error": "true", "msg": "request not in json format"}), 400

    current_userid = get_jwt_identity()
    password = request.json.get("password")
    password_confirm = request.json.get("password_confirm")

    user = User.query.filter_by(id=current_userid).first()
    
    if password is not None and password_confirm is not None:
        if password == password_confirm:
            if not user.verify_password(password):
                user.set_password(password)
                db.session.commit()
                return jsonify({'msg': 'password changed'}), 200
            else:
                return jsonify({'error': 'true', 'msg': 'same password'}), 400
        else:
            return jsonify({'error': 'true', 'msg': 'password != password_confirm'}), 400
    else:
        return jsonify({'error': 'true', 'msg': 'password not given'}), 400


#requires login
@login_route.route("/api/user/team", methods=["UPDATE"])
@jwt_required()
def update_team():
    if not request.is_json:
        return jsonify({"error": "true", "msg": "request not in json format"}), 400

    current_userid = get_jwt_identity()
    team = request.json.get("team")

    user = User.query.filter_by(id=current_userid).first()
        
    if team is not None: 
        if team in TEAM_LIST:
            if user.team != team:
                user.set_team(team)
                db.session.commit()
                return jsonify({'msg': 'team changed'}), 200
            else:
                return jsonify({'error': 'true', 'msg': 'same team'}), 400
        else:
            return jsonify({'error': 'true', 'msg': 'team not found'}), 400
    else:
        return jsonify({'error': 'true', 'msg': 'team not given'}), 400