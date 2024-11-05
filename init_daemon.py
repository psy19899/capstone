import threading 
from bots.daemon import *
import time 
import requests 

print("[*] init_daemon file executing")

while True:
    try:
        res = requests.get("http://220.88.39.23:5000/health")
        print(res.text)
        if "hello" in res.text: 
            break 
    except:
        time.sleep(60*5)
    

print("[*] calendar daemon started")
calendar_daemon = threading.Thread(target=calendar_daemon_func)
calendar_daemon.daemon = True 
calendar_daemon.start()

print("[*] news daemon started")
news_daemon = threading.Thread(target=news_daemon_func)
news_daemon.daemon = True 
news_daemon.start()

print("[*] stats_daemon started")
stats_daemon = threading.Thread(target=stats_daemon_func)
stats_daemon.daemon = True 
stats_daemon.start()

print("[*] players_daemon started")
players_daemon = threading.Thread(target=players_daemon_func)
players_daemon.daemon = True 
players_daemon.start()

while True:
    time.sleep(1)