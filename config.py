from datetime import datetime 
import os 

class Config:
    DB_username = os.getenv('MYSQL_USER')
    DB_password = os.getenv('MYSQL_PASSWORD')
    DB_host = os.getenv('MYSQL_HOST')
    DB_port = os.getenv('MYSQL_PORT')
    DB_dbname = os.getenv('MYSQL_DATABASE')
    ADMIN_KEY = os.getenv("ADMIN_KEY")

    DAEMON_news_refresh_time = 60*5 #5분
    DAEMON_calendar_refresh_time = 60*60*24*7 #7일
    DAEMON_stats_refresh_time = 60*60*24*8 #8일
    DAEMON_players_refresh_time = 60*60*24*15 #15일
    
    SERVER_port = 5000

    JWT_SECRET_KEY = '123'
    JWT_ACCESS_TOKEN_EXPIRES = False #access token does not expire

    max_traversal = 5

    default_match_reservation_url = 'https://www.kleague.com/schedule.do'