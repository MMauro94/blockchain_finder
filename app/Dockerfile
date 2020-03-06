FROM python:3.7

RUN apt -y update && apt install -y libleveldb-dev

ADD ./src/requirements.txt /app/requirements.txt
RUN pip install -r /app/requirements.txt
RUN pip install uwsgi

CMD uwsgi --http 0.0.0.0:8080 --wsgi-file /app/finder.py --callable app --threads 8 --stats 0.0.0.0:9191