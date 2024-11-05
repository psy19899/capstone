THIS_SEASON_TEAM_LIST = [
    '울산', '김천', '수원FC', '포항', '서울', '광주', '제주', '대전', '전북', 
    '대구', '인천', '강원'
]
NEWS_CATEGORY_LIST = ["interview", "match_result","match_plan","club_internal","player_idv","issue","trade","squad","injury"]
TEAM_LIST = [
    '울산', '김천', '수원FC', '포항', '서울', '광주', '제주', '대전', '전북', '대구', 
    '인천', '강원', '수원', '성남', '안양', '경남', '김포', '부산', '부천', '안산',
    '전남', '천안', '충남', '충북', '상주'
]
TEAM_DICT = {
    '울산': 'K01', '김천': 'K35', '수원FC': 'K29', '포항': 'K03', '서울': 'K09', 
    '광주': 'K22', '제주': 'K04', '대전': 'K10', '전북': 'K05', "대구": "K17", 
    "인천": 'K18', '강원': 'K21', '수원': 'K02', '성남': 'K08', '안양': 'K27',
    '경남': 'K20', '김포': 'K36', '부산': 'K06', '부천': 'K26', '안산': 'K32',
    '전남': 'K07', '천안': 'K38', '충남': 'K34', '충북': 'K37', '상주': 'K23'
}

STAT_FEATURES_training = ['assists', 'total_shootings', 'shots_on_target', 'shots_blocked',
       'shots_out_of_bounds', 'shots_in_PA', 'shots_out_PA', 'offsides',
       'freekicks_on_target', 'freekicks_on_cross', 'cornerkicks', 'throwins',
       'dribbles', 'tot_passes', 'passes_critical', 'passes_in_defense_area',
       'passes_long_range', 'passes_short_range', 'passes_forward',
       'passes_middle_range', 'passes_horizontal', 'passes_backward',
       'passes_crosses', 'passes_in_attack_area', 'passes_in_middle_area',
       'tackles', 'fights_air', 'fights_ground', 'ball_intercepts',
       'ball_clearings', 'ball_cuts', 'ball_gains', 'ball_blocks',
       'ball_misses', 'fouls_against_other_team', 'fouls_against_own_team',
       'yellow_cards', 'red_cards', 'goalkeeper_catchings',
       'goalkeeper_punchings', 'goalkeeper_goalkicks',
       'goalkeeper_air_clearings'
]

STAT_FEATURES = ['goals', 'assists', 'total_shootings', 'shots_on_target', 'shots_blocked', 'shots_out_of_bounds', 'shots_in_PA', 'shots_out_PA', 'offsides', 'freekicks_on_target', 'freekicks_on_cross', 'cornerkicks', 'throwins', 'dribbles', 'tot_passes', 'passes_critical', 'passes_in_defense_area', 'passes_long_range', 'passes_short_range', 'passes_forward', 'passes_middle_range', 'passes_horizontal', 'passes_backward', 'passes_crosses', 'passes_in_attack_area', 'passes_in_middle_area', 'dismarks', 'tackles', 'fights_air', 'fights_ground', 'ball_intercepts', 'ball_clearings', 'ball_cuts', 'ball_gains', 'ball_blocks', 'ball_misses', 'fouls_against_other_team', 'fouls_against_own_team', 'yellow_cards', 'red_cards', 'goals_conceded', 'goalkeeper_catchings', 'goalkeeper_punchings', 'goalkeeper_goalkicks', 'goalkeeper_air_clearings']
STAT_FEATURES_KOR = ['득점', '도움', '슈팅', '유효슈팅', '블락된 슈팅', '벗어난 슈팅', 'PA내 슈팅', 'PA외 슈팅', '오프사이드', '프리킥 유효슈팅', '프리킥 크로스', '코너킥', '스로인', '드리블', '패스', '키패스', '수비진영 패스', '롱패스', '단거리패스', '전방패스', '중거리패스', '횡패스', '후방패스', '크로스', '공격진영 패스', '중앙지역 패스', '탈압박', '태클', '경합(공중 )', '경합(지상 )', '인터셉트', '클리어링', '차단', '획득', '블락', '볼미스', '파울', '피파울', '경고', '퇴장', '실점', '캐칭', '펀칭', '골킥', '공중 클리어링']
STAT_FEATURES_DICT = {
    '득점': 'goals',
    '도움': 'assists',
    '슈팅': 'total_shootings',
    '유효슈팅': 'shots_on_target',
    '블락된 슈팅': 'shots_blocked',
    '벗어난 슈팅': 'shots_out_of_bounds',
    'PA내 슈팅': 'shots_in_PA',
    'PA외 슈팅': 'shots_out_PA',
    '오프사이드': 'offsides',
    '프리킥 유효슈팅': 'freekicks_on_target',
    '프리킥 크로스': 'freekicks_on_cross',
    '코너킥': 'cornerkicks',
    '스로인': 'throwins',
    '드리블': 'dribbles',
    '패스': 'tot_passes',
    '키패스': 'passes_critical',
    '수비진영 패스': 'passes_in_defense_area',
    '롱패스': 'passes_long_range',
    '단거리패스': 'passes_short_range',
    '전방패스': 'passes_forward',
    '중거리패스': 'passes_middle_range',
    '횡패스': 'passes_horizontal',
    '후방패스':'passes_backward',
    '크로스':'passes_crosses',
    '공격진영 패스':'passes_in_attack_area',
    '중앙지역 패스':'passes_in_middle_area',
    '탈압박': 'dismarks',
    '태클':'tackles',
    '경합(공중)': 'fights_air',
    '경합(지상)': 'fights_ground',
    '인터셉트': 'ball_intercepts',
    '클리어링': 'ball_clearings',
    '차단': 'ball_cuts',
    '획득':'ball_gains',
    '블락':'ball_blocks',
    '볼미스':'ball_misses',
    '파울':'fouls_against_other_team',
    '피파울':'fouls_against_own_team',
    '경고':'yellow_cards',
    '퇴장':'red_cards',
    '실점':'goals_conceded',
    '캐칭':'goalkeeper_catchings',
    '펀칭':'goalkeeper_punchings',
    '골킥':'goalkeeper_goalkicks',
    '공중 클리어링':'goalkeeper_air_clearings'
}