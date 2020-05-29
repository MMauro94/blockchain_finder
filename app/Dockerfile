FROM python:3.7

RUN apt -y update && apt install -y libleveldb-dev munin-node

ADD ./src/requirements.txt /app/requirements.txt
RUN pip install -r /app/requirements.txt
RUN pip install uwsgi
RUN pip install gunicorn

ADD ./munin.conf /etc/munin/munin-node.conf
ADD ./run.sh /run.sh
CMD chmod +x /run.sh

RUN echo -e "[iostat]\n\tenv.SHOW_NUMBERED 1" >> /etc/munin/plugin-conf.d/munin-node

RUN ln -s /usr/share/munin/plugins/iostat /etc/munin/plugins/iostat
RUN ln -s /usr/share/munin/plugins/iostat_ios /etc/munin/plugins/iostat_ios
RUN apt install -y gdb


WORKDIR /app
CMD /run.sh