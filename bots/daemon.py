from extensions import admin_token
from config import Config 
import requests 
import time 
import os 
import hashlib
from bots.crawler import * 

"""
def set_admin_key():
    random_bytes = os.urandom(64)
    secret_key = hashlib.sha256(random_bytes).hexdigest()
    os.environ['ADMIN_KEY'] = secret_key
    return secret_key

secret_key = "66d4d27d0b49b1009c39a826b8ec88a7b0aabb5115dc843201e40c989216e8d4"
"""

def news_daemon_func():
    while True:
        try:
            time.sleep(Config.DAEMON_news_refresh_time)
            Crawler_News(modes='today').fetch()
            """
            headers = {'Authorization': secret_key}
            response = requests.get(f"http://220.88.39.23:{Config.SERVER_port}/crawling/fetch_today_news", headers=headers)
            """
        except Exception as e:
            print(f"[-] Error : {e}")

def calendar_daemon_func():
    while True:
        try: 
            time.sleep(Config.DAEMON_calendar_refresh_time)
            Crawler_Calendars(for_training=False).fetch()
            """
            headers = {'Authorization': secret_key}
            response = requests.get(f"http://220.88.39.23:{Config.SERVER_port}/crawling/fetch_calendar", headers=headers)
            """
        except Exception as e:
            print(f"[-] Error : {e}")

def stats_daemon_func():
    while True:
        try: 
            time.sleep(Config.DAEMON_stats_refresh_time)
            Crawler_Stats().fetch()
            """
            headers = {'Authorization': secret_key}
            response = requests.get(f"http://220.88.39.23:{Config.SERVER_port}/crawling/fetch_stats", headers=headers)
            """
        except Exception as e:
            print(f"[-] Error : {e}")

def players_daemon_func():
    while True:
        try: 
            time.sleep(Config.DAEMON_players_refresh_time)
            Crawler_Players().fetch()
            """
            headers = {'Authorization': secret_key}
            response = requests.get(f"http://220.88.39.23:{Config.SERVER_port}/crawling/fetch_players", headers=headers)
            """
        except Exception as e:
            print(f"[-] Error : {e}")