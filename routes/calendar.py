from flask import request, Blueprint, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models.team import Team, Calendar
from models.users import User
from datetime import datetime 
from sqlalchemy import func 

calendar_route = Blueprint('calendar_route', __name__)
@calendar_route.route("/api/calendar/planned_events", defaults={'match_date': None}, methods=['GET'])
@calendar_route.route("/api/calendar/planned_events/<match_date>", methods=['GET'])
@jwt_required()
def planned_events(match_date):
    userid = get_jwt_identity()
    user = User.query.filter_by(id=userid).first()
    if user is None:
        return jsonify({'msg': 'something went wrong'})

    team_name = user.team 

    team = Team.query.filter_by(team_name=team_name).first()

    if team is None:
        return jsonify({'msg': 'no team found'}), 400

    if match_date is not None:
        try:
            match_date = datetime.strptime(match_date, "%Y%m%d")
        except ValueError: 
            return jsonify({"msg": "date must be %Y%m%d%H%M (ex. 19990125)"})

        matches = Calendar.query.filter(Calendar.is_past_game==False, Calendar.team_id==team.id, func.DATE(Calendar.match_date)==match_date).all() 
        if matches is None or len(matches) == 0:
            return jsonify({"msg": "match not exist"})
        return jsonify([match.to_dict_planned() for match in matches])
    
    matches = Calendar.query.filter_by(is_past_game=False, team_id=team.id).order_by(Calendar.match_date).all()

    if len(matches) == 0:
        return jsonify({'msg': 'no match planned'})
    else:
        res = {}
        for i, match in enumerate(matches):
            res[i] = match.to_dict_planned()
        return jsonify(res)

@calendar_route.route("/api/calendar/past_events", defaults={"match_date": None}, methods=['GET'])
@calendar_route.route("/api/calendar/past_events/<match_date>", methods=['GET'])
@jwt_required()
def past_events(match_date):
    userid = get_jwt_identity()
    user = User.query.filter_by(id=userid).first() 
    if user is None:
        return jsonify({"msg": "something wnet wrong"})
    
    team_name = user.team 
    team = Team.query.filter_by(team_name=team_name).first()

    if team is None:
        return jsonify({"msg": "team not found"})

    if match_date is not None: 
        try:
            match_date = datetime.strptime(match_date, "%Y%m%d")
        except ValueError: 
            return jsonify({"msg": "date must be %Y%m%d (ex. 19990125)"})

        matches = Calendar.query.filter(Calendar.is_past_game==True, Calendar.team_id==team.id, func.DATE(Calendar.match_date)==match_date).all() 
        if matches is None or len(matches) == 0:
            return jsonify({"msg": "match not exist"})
        return jsonify([match.to_dict_past() for match in matches])

    matches = Calendar.query.filter_by(team_id=team.id, is_past_game=True).order_by(Calendar.match_date).all()

    if len(matches) == 0:
        return jsonify({"msg": "past_events 0"})
    else:
        res = {}
        for i, match in enumerate(matches):
            res[i] = match.to_dict_past()
        return jsonify(res)