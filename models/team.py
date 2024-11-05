from extensions import app, db
from config import Config 
from Dict import STAT_FEATURES_training

class Team(db.Model):
    __tablename__ = 'teams'
    __table_args__ = {
        'mysql_charset': 'utf8mb4',
        'mysql_collate': 'utf8mb4_unicode_ci' 
    }
    id = db.Column(db.Integer, primary_key = True)
    team_name = db.Column(db.Text, nullable=False)
    
    is_member_fetched = db.Column(db.Boolean, default=False, nullable=True)

    members = db.relationship('Member', backref='team', lazy=True) #Member에서 team으로 Team에 접근할 수 있음
    calendars = db.relationship('Calendar', backref='team', lazy=True)
    stats = db.relationship('Stat', backref='team', lazy=True)

class Member(db.Model):
    __tablename__ = 'teams_members'
    __table_args__ = {
        'mysql_charset': 'utf8mb4',
        'mysql_collate': 'utf8mb4_unicode_ci' 
    }
    id = db.Column(db.Integer, primary_key = True)
    member_name = db.Column(db.Text, nullable=True)
    role = db.Column(db.Text, nullable=True)
    back_number = db.Column(db.Integer, nullable=True)

    team_id = db.Column(db.Integer, db.ForeignKey('teams.id'), nullable=False)

class Calendar(db.Model):
    __tablename__ = 'teams_calendar'
    __table_args__ = {
        'mysql_charset': 'utf8mb4',
        'mysql_collate': 'utf8mb4_unicode_ci' 
    }
    id = db.Column(db.Integer, primary_key = True)
    match_date = db.Column(db.DateTime, nullable=True)
    round_num = db.Column(db.Integer, nullable=True)
    opponent_team = db.Column(db.Text, nullable=True)
    location = db.Column(db.Text, nullable=True)
    reservation_url = db.Column(db.Text, default=Config.default_match_reservation_url, nullable=True)
    is_past_game = db.Column(db.Boolean, nullable=True)
    this_score = db.Column(db.Integer, nullable=True)
    opponent_score = db.Column(db.Integer, nullable=True)
    
    team_id = db.Column(db.Integer, db.ForeignKey('teams.id'), nullable=True)

    def to_dict_past(self):
        res = {}
        res['match_date'] = getattr(self, 'match_date').strftime("%Y-%m-%d %H:%M")
        res['opponent_team'] = getattr(self, 'opponent_team')
        res['location'] = getattr(self, 'location')
        res['this_score'] = getattr(self, 'this_score')
        res['opponent_score'] = getattr(self, 'opponent_score')
        return res 
    def to_dict_planned(self):
        res = {}
        res['match_date'] = getattr(self, 'match_date').strftime("%Y-%m-%d %H:%M")
        res['opponent_team'] = getattr(self, 'opponent_team')
        res['location'] = getattr(self, 'location')
        res['reservation_url'] = getattr(self, 'reservation_url')
        return res 

class Stat(db.Model):
    __tablename__ = 'teams_stats'
    __table_args__ = {
        'mysql_charset': 'utf8mb4',
        'mysql_collate': 'utf8mb4_unicode_ci' 
    }
    id = db.Column(db.Integer, primary_key = True)
    year = db.Column(db.Integer, nullable=True)
    round_num = db.Column(db.Integer, nullable=True)
    tmp_team_name = db.Column(db.String(10), nullable=True)
    opponent = db.Column(db.Text, nullable=True)

    goals = db.Column(db.Integer, nullable=True) 
    assists = db.Column(db.Integer, nullable=True)
    total_shootings = db.Column(db.Integer, nullable=True)
    shots_on_target = db.Column(db.Integer, nullable=True)
    shots_blocked = db.Column(db.Integer, nullable=True)
    shots_out_of_bounds = db.Column(db.Integer, nullable=True)
    shots_in_PA = db.Column(db.Integer, nullable=True)
    shots_out_PA = db.Column(db.Integer, nullable=True)
    offsides = db.Column(db.Integer, nullable=True)
    freekicks_on_target = db.Column(db.Integer, nullable=True)
    freekicks_on_cross = db.Column(db.Integer, nullable=True)
    cornerkicks = db.Column(db.Integer, nullable=True)
    throwins = db.Column(db.Integer, nullable=True)
    dribbles = db.Column(db.Integer, nullable=True)
    tot_passes = db.Column(db.Integer, nullable=True)
    passes_critical = db.Column(db.Integer, nullable=True)
    passes_in_defense_area = db.Column(db.Integer, nullable=True)
    passes_long_range = db.Column(db.Integer, nullable=True)
    passes_short_range = db.Column(db.Integer, nullable=True)
    passes_forward = db.Column(db.Integer, nullable=True)
    passes_middle_range = db.Column(db.Integer, nullable=True)
    passes_horizontal = db.Column(db.Integer, nullable=True)
    passes_backward = db.Column(db.Integer, nullable=True)
    passes_crosses = db.Column(db.Integer, nullable=True)
    passes_in_attack_area = db.Column(db.Integer, nullable=True)
    passes_in_middle_area = db.Column(db.Integer, nullable=True)
    dismarks = db.Column(db.Integer, nullable=True)
    tackles = db.Column(db.Integer, nullable=True)
    fights_air = db.Column(db.Integer, nullable=True)
    fights_ground = db.Column(db.Integer, nullable=True)
    ball_intercepts = db.Column(db.Integer, nullable=True)
    ball_clearings = db.Column(db.Integer, nullable=True)
    ball_cuts = db.Column(db.Integer, nullable=True)
    ball_gains = db.Column(db.Integer, nullable=True)
    ball_blocks = db.Column(db.Integer, nullable=True)
    ball_misses = db.Column(db.Integer, nullable=True)
    fouls_against_other_team = db.Column(db.Integer, nullable=True)
    fouls_against_own_team = db.Column(db.Integer, nullable=True)
    yellow_cards = db.Column(db.Integer, nullable=True)
    red_cards = db.Column(db.Integer, nullable=True)
    goals_conceded = db.Column(db.Integer, nullable=True)
    goalkeeper_catchings = db.Column(db.Integer, nullable=True)
    goalkeeper_punchings = db.Column(db.Integer, nullable=True)
    goalkeeper_goalkicks = db.Column(db.Integer, nullable=True)
    goalkeeper_air_clearings = db.Column(db.Integer, nullable=True)
    win = db.Column(db.String(10), nullable=True)

    team_id = db.Column(db.Integer, db.ForeignKey('teams.id'), nullable=False)

    def to_list(self):
        return [getattr(self, column.name) for column in self.__table__.columns if column.name in STAT_FEATURES_training]
    def to_dict(self):
        return {column.name: getattr(self, column.name) for column in self.__table__.columns if column.name != 'team_id' and column.name != 'id'}