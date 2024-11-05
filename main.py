from extensions import app, admin_token
from flask_sqlalchemy import SQLAlchemy
from config import Config
from extensions import *


@jwt.token_in_blocklist_loader
def check_if_token_is_revoke(jwt_header, jwt_payload):
    jti = jwt_payload['jti']
    return jti in jwt_blocklist

#register all the routes 
from routes.login import login_route 
from routes.news import news_route 
from routes.calendar import calendar_route
from routes.stats import stats_route
from routes.predict import prediction_route
from routes.bots_routes import crawling_routes

app.register_blueprint(login_route)
app.register_blueprint(news_route)
app.register_blueprint(calendar_route)
app.register_blueprint(stats_route)
app.register_blueprint(prediction_route)
app.register_blueprint(crawling_routes)

@app.before_request
def log_request_info():
    if request.headers.getlist("X-Forwarded-For"):
        ip_address = request.headers.getlist("X-Forwarded-For")[0]
    else:
        ip_address = request.remote_addr
    app.logger.info(
    "IP: %s | Method: %s | Path: %s", ip_address, request.method, request.path,
    )

@app.after_request
def log_response_info(response):
    if request.headers.getlist("X-Forwarded-For"):
        ip_address = request.headers.getlist("X-Forwarded-For")[0]
    else:
        ip_address = request.remote_addr
    app.logger.info(
        "IP: %s | Method: %s | Path: %s | Status: %s", ip_address,request.method, request.path, response.status
    )
    return response
    
#docker network create my_net
#docker run -d --network my_net -p 5000:5000 -v C:\Users\user\Desktop\종설:/app my_app
#docker run -d --network my_net --name my_app_db -p 3308:3308 my_app_db
from bots.crawler import * 
if __name__ == '__main__':
    app.run(host='0.0.0.0')