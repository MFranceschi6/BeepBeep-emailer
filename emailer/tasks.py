from celery import Celery
from celery.schedules import crontab
import os
from emailer.mail_service import MailService

BACKEND = BROKER = 'redis://' + os.environ[
    'REDIS'] + ":6379" if 'REDIS' in os.environ else "redis://127.0.0.1:6379"
celery = Celery(__name__, backend=BACKEND, broker=BROKER)
__mail_service = MailService()


celery.conf.timezone = 'Europe/Rome'
celery.conf.beat_schedule = {
    'send_reports-every-midnight': {
        'task': 'emailer.tasks.send_reports',
        'schedule': crontab(hour = 0, minute = 0)
    }
}

celery.conf.task_routes = {'emailer.tasks.send_reports': {'queue': 'email'}}


@celery.task()
def send_reports():
    __mail_service.sendReports()


if __name__ == '__main__':
    send_reports()
