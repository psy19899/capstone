from flask import Blueprint, request
from flask import jsonify
from bots.crawler import Crawler_Calendars, Crawler_News, Crawler_Stats, Crawler_Players
crawling_routes = Blueprint('team_crawling_route', __name__)
import os 

secret_key = "66d4d27d0b49b1009c39a826b8ec88a7b0aabb5115dc843201e40c989216e8d4"

def is_admin(): 
    header = request.headers.get('Authorization')
    if not header:
        return False 
    
    if header == secret_key:
        return True 

    return False 

@crawling_routes.route('/crawling/fetch_calendar', methods=['GET'])
def fetch_calendar():
    if not is_admin():
        return
    
    Crawler_Calendars(for_training=False).fetch()

    return jsonify({'msg': 'fetched calendar'})

@crawling_routes.route('/crawling/fetch_today_news', methods=['GET'])
def fetch_today_news():
    if not is_admin():
        return
    
    Crawler_News(modes='today').fetch()
    
    print("[*] fetch_today_news finished")

    return jsonify({'msg': 'fetched news'})

@crawling_routes.route('/crawling/fetch_stats', methods=['GET'])
def fetch_stats():
    if not is_admin():
        return
    
    Crawler_Stats().fetch()

    return jsonify({'msg': 'fetched stats'})

@crawling_routes.route('/crawling/fetch_players', methods=['GET'])
def fetch_players():
    if not is_admin():
        return
    
    Crawler_Players().fetch()

    return jsonify({'msg': 'fetched players'})