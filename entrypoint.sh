#!/bin/sh
echo "[*] flask migration started"
flask db stamp head 
flask db migrate
flask db upgrade


echo "[*] init_db.py started"
python3 init_db.py

: '
echo "[*] init_daemon.py started in background"
python3 init_daemon.py &
'

gunicorn --reload -w 6 --worker-class gthread -b 0.0.0.0:5000 main:app