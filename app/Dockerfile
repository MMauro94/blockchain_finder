FROM python:3.7

RUN apt -y update && apt install -y libleveldb-dev

ADD ./src/requirements.txt /app/requirements.txt
RUN pip install -r /app/requirements.txt

CMD python /app/finder.py