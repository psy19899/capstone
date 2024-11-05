from flask_sqlalchemy import SQLAlchemy
from flask import Flask 
from flask_jwt_extended import create_access_token
from flask_jwt_extended import JWTManager
from flask_migrate import Migrate 
from config import Config
from flask_cors import CORS 
from flask import Flask, request
import logging

app = Flask(__name__)

# 로그 파일 설정
logging.basicConfig(
        filename='access.log',
            level=logging.INFO, 
                format='%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'  # 로그 형식
)


#!adjust the resources CORS(app, resources={"origins": "http://220.88.39.23:80"})
CORS(app)


#db credentials 
user = Config.DB_username
pwd = Config.DB_password
host = Config.DB_host
port = Config.DB_port
db_name = Config.DB_dbname
db_url = f"mysql+pymysql://{user}:{pwd}@{host}:{port}/{db_name}?charset=utf8mb4"

app.config['SQLALCHEMY_DATABASE_URI'] = db_url 
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False 

db = SQLAlchemy()
db.init_app(app)
migrate = Migrate(app, db)

#jwt
app.config['JWT_SECRET_KEY'] = Config.JWT_SECRET_KEY
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = Config.JWT_ACCESS_TOKEN_EXPIRES
jwt = JWTManager(app)
jwt_blocklist = set()


admin_token = None
with app.app_context():
    admin_token = create_access_token(identity='admin')