#!/bin/bash

munin-node

gunicorn -b 0.0.0.0:8081 -w 1 -t 0 --backlog 1024 --log-level debug finder:app
#uwsgi --http 0.0.0.0:8081 --wsgi-file /app/finder.py --callable app --threads 1 -l 128 --stats 0.0.0.0:9191 -t 0 --harakiri-verbose --socket-timeout 0 --http-timeout 0
#python /app/finder.py