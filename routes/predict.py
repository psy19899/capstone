from flask import Blueprint, request, jsonify
from AI.train import Stat_Predictor
from Dict import THIS_SEASON_TEAM_LIST
from flask_jwt_extended import jwt_required, get_jwt_identity
from models.users import User 
from models.team import Calendar, Team

prediction_route = Blueprint('prediction_route', __name__)


@prediction_route.route("/api/predict", defaults={"opponent": None}, methods=['GET'])
@prediction_route.route("/api/predict/<opponent>", methods=['GET'])
@jwt_required()
def predict(opponent):
    userid = get_jwt_identity()
    user = User.query.filter_by(id=userid).first()
    if user is None:
        return jsonify({"msg": 'something wnet wrong'})
    
    if opponent is not None: 
        if opponent == 'nearest': 
            team_A = user.team 
            team = Team.query.filter_by(team_name=team_A).first() 
            if team is None:
                return jsonify({"msg": "team A not exist"})

            calendars = [calendar for calendar in team.calendars if calendar.is_past_game==False]
            nearest_match = sorted(calendars, key=lambda x: x.match_date)[0]
            if nearest_match is None: 
                return jsonify({"msg": "team B not exist"})

            team_B = nearest_match.opponent_team
        else:
            if opponent not in THIS_SEASON_TEAM_LIST:
                return jsonify({"msg": "team not exist", "team_list": THIS_SEASON_TEAM_LIST})

            team_A, team_B = user.team, opponent
        label = Stat_Predictor(team_A, team_B).predict()
        return jsonify({"teamA": team_A, "teamB": team_B, 'result': label})
        
    team_A = request.args.get('team_A')
    team_B = request.args.get('team_B')
    
    if team_A is None or team_B is None: 
        return jsonify({"msg": "team not exist"})
    if team_A not in THIS_SEASON_TEAM_LIST or team_B not in THIS_SEASON_TEAM_LIST: 
        return jsonify({"msg": "teamnames not exist in db", "team_list": THIS_SEASON_TEAM_LIST})
    
    label = Stat_Predictor(team_A, team_B).predict()
    return jsonify({"teamA": team_A, "teamB": team_B, 'result': label})