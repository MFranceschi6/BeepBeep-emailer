from celery import Celery
from celery.schedules import crontab
import os
import datetime
from mail_service import MailService

BACKEND = BROKER = 'redis://' + os.environ[
    'REDIS'] + ":6479" if 'DATASERVICE' in os.environ else "redis://127.0.0.1:6479"
celery = Celery(__name__, backend=BACKEND, broker=BROKER)
__mail_service = MailService()


celery.conf.timezone = 'Europe/Rome'
celery.conf.beat_schedule = {
    'send_reports-every-midnight': {
        'task': 'emailer.emailer.send_reports',
        'schedule': crontab(hour = 0, minute = 0)
    }
}


@celery.task()
def send_reports():
    __mail_service.sendReports()


if __name__ == '__main__':
    send_reports()