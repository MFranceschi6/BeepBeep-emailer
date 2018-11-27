import os
import smtplib
import datetime
import requests
import monthdelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from email.utils import make_msgid
from emailer.request_utils import get_request_retry, users_endpoint, runs_endpoint

DATA_SERVICE = "http://" + os.environ[
    'DATASERVICE'] + ':5002' if 'DATASERVICE' in os.environ else "http://127.0.0.1:5002"


class MailService:

    def __init__(self):

        # Server config
        self.__website = os.environ['WEBSITE_NAME']
        self.__group = os.environ['GROUP_NAME']
        self.__mail_subject = os.environ['MAIL_REPORT_SUBJECT']
        self.__message_no_run = os.environ['MAIL_MESSAGE_NO_RUN']

        # SMTP Server
        gmail_user = os.environ['MAIL_GMAIL_USER']
        gmail_pass = os.environ['MAIL_GMAIL_PASS']
        self.__server = smtplib.SMTP('smtp.gmail.com', 587)
        self.__server.ehlo()
        self.__server.starttls()
        self.__server.login(gmail_user, gmail_pass)

        self.__base_folder = 'emailer/static/mail'

        # Templates
        self.__content = 'content_template.html'
        self.__report_no_run = 'report_no_run_template.html'
        self.__report_run = 'report_run_template.html'
        templates_filenames = [self.__content,
                               self.__report_no_run,
                               self.__report_run]
        self.__templates = dict.fromkeys(templates_filenames)

        # Images
        self.__logo = '_logo.png'
        self.__params = '_params.png'
        self.__github = '_github.png'
        images_filenames = [self.__logo,
                            self.__params,
                            self.__github]
        self.__images = dict.fromkeys(images_filenames)
        self.__images_CID = dict.fromkeys(images_filenames)

        self.__loadTemplates()
        self.__loadImages()
        self.__updateToday()

    def __loadFile(self, filename, flags):
        with open(self.__base_folder + '/' + filename, flags) as f:
            data = f.read()
            f.close()
        return data

    def __loadTemplates(self):
        for filename in self.__templates.keys():
            self.__templates[filename] = self.__loadFile(filename, 'r').replace('\n', '')

    def __loadMIMEImage(self, filename):
        imageData = self.__loadFile(filename, 'rb')
        imageCID = make_msgid()[1:-1]
        imageMIME = MIMEImage(imageData, 'png')
        imageMIME.add_header('Content-ID', '<{}>'.format(imageCID))
        imageMIME.add_header('Content-Disposition', 'inline', filename=filename)

        return imageMIME, imageCID

    def __loadImages(self):
        for filename in self.__images.keys():
            self.__images[filename], self.__images_CID[filename] = self.__loadMIMEImage(filename)

    # TODO: refactoring
    def __getDeltaFromPeriodicity(self, periodicity):

        delta = datetime.timedelta(seconds=0)

        if periodicity == 'Daily':
            delta = datetime.timedelta(days=1)
        elif periodicity == 'Weekly':
            delta = datetime.timedelta(days=7)
        elif periodicity == 'Monthly':
            delta = monthdelta.Monthdelta(1)

        return delta

    def __getUserReportResult(self, user):
        report_periodicity = user['report_periodicity']

        delta = self.__getDeltaFromPeriodicity(report_periodicity)
        endDate = self.__today
        startDate = endDate - delta

        try:
            print(user['id'])
            runs = get_request_retry(runs_endpoint(user['id']), params={'start-date': startDate.strftime('%Y-%m-%dT%H'
                                                                                                         ':%M:%SZ'),
                                                                        'finish-date': endDate.strftime('%Y-%m-%dT%H:%M'
                                                                                                        ':%SZ')
                                                                        })

        except requests.exceptions.RequestException:
            print("DATASERVICE unavailable can't send mail")
            return None

        result = {'total_distance': 0}
        tot_speed = 0
        count = 0
        for run in runs.json():
            result['total_distance'] += run['distance']
            tot_speed += run['average_speed']
            count += 1
        if count > 0:
            result['avg_speed'] = float('%.2f' % (tot_speed / count))
        else:
            result['avg_speed'] = float(0)
        return result

    def __createMIMEContent(self, user):
        result = self.__getUserReportResult(user)
        if result is None:
            return None
        if result['total_distance'] == 0:
            template = self.__templates[self.__report_no_run]
            result_content = template.format(
                message=self.__message_no_run
            )
        else:
            template = self.__templates[self.__report_run]
            result_content = template.format(
                total_distance=result['total_distance'],
                avg_speed=result['avg_speed']
            )

        template = self.__templates[self.__content]
        content = template.format(
            website=self.__website,
            group=self.__group,
            periodicity=user['report_periodicity'],
            result=result_content,
            cid_logo=self.__images_CID[self.__logo],
            cid_params=self.__images_CID[self.__params],
            cid_github=self.__images_CID[self.__github]
        )
        return MIMEText(content, 'html')

    def __sendMail(self, user):
        msg = MIMEMultipart('related')

        msg['Subject'] = self.__mail_subject
        msg['From'] = self.__website
        msg['To'] = user['email']

        contentMIME = self.__createMIMEContent(user)
        if contentMIME is None:
            return
        msg.attach(contentMIME)

        for imageMIME in self.__images.values():
            msg.attach(imageMIME)

        try:
            self.__server.sendmail(
                msg['From'],
                msg['To'],
                msg.as_string()
            )
            print("Email sent to %s" % msg['To'])
        except Exception as exception:
            print("Error: %s!\n\n" % exception)

    def __updateToday(self):
        self.__today = datetime.datetime.today().replace(hour=0, minute=0, second=0)

    def sendReports(self):
        print("Sending reports...")

        try:
            res = get_request_retry(users_endpoint())
        except requests.exceptions.RequestException:
            print("DATASERVICE Unavailable")
            pass
        users = res.json()
        self.__updateToday()
        for user in users['users']:
            print(user)
            # Not set
            if user['report_periodicity'] == 'No':
                pass
            # Daily
            if user['report_periodicity'] == 'Daily':
                self.__sendMail(user)
            # Weekly
            elif user['report_periodicity'] == 'Weekly' and self.__today.isoweekday() == 1:
                self.__sendMail(user)
            # Monthly
            elif user['report_periodicity'] == 'Monthly' and self.__today.day == 1:
                self.__sendMail(user)
