FROM python:3.6.7-jessie
MAINTAINER "Butter Group"
ADD requirements.txt ./app/
WORKDIR /app
RUN pip install -r requirements.txt
ADD . /app
CMD ["celery","-A", "emailer.tasks", "worker", "-q", "email", "-B", "-l", "info", "-s", "./schedule-db"]