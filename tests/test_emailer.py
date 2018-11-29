import pytest
from unittest import mock
from emailer.mail_service import *
from datetime import datetime


# Test if the method for sending reports is indeed invoked
def test_send_mail_to_user_no_runs():
    with mock.patch("emailer.mail_service.get_request_retry") as mocked:
        mocked.return_value.status_code = 200
        mocked.return_value.json.return_value = {
            'users':
                [
                    {
                        "age": 42,
                        "email": "example@example.com",
                        "firstname": "Admin",
                        "id": 1,
                        "lastname": "Admin",
                        "max_hr": 180,
                        "rest_hr": 50,
                        "vo2max": 63.0,
                        "weight": 60.0,
                        "report_periodicity": "No"
                    }
                ]}

        mailservice = MailService()
        mailservice.sendReports()

        assert mocked.return_value.json.call_count == 1


def test_send_mail_to_multiple_users_no_runs():
    with mock.patch("emailer.mail_service.get_request_retry") as mocked:
        mocked.return_value.status_code = 200
        mocked.return_value.json.return_value = {
            'users':
                [
                    {
                        "age": 42,
                        "email": "example@example.com",
                        "firstname": "Admin",
                        "id": 1,
                        "lastname": "Admin",
                        "max_hr": 180,
                        "rest_hr": 50,
                        "vo2max": 63.0,
                        "weight": 60.0,
                        "report_periodicity": "No"
                    },
                    {
                        "age": 43,
                        "email": "example@example.com",
                        "firstname": "Admin",
                        "id": 2,
                        "lastname": "Admin",
                        "max_hr": 180,
                        "rest_hr": 50,
                        "vo2max": 63.0,
                        "weight": 60.0,
                        "report_periodicity": "No"
                    }
                ]}

        with mock.patch('emailer.mail_service.smtplib.SMTP') as mockedMail:
            mailservice = MailService()
            mailservice.sendReports()
            # we have successfully sent an email
            assert mockedMail.call_count == 1


class FakeUserResponse:
    def __init__(self, report_periodicity):
        self.status_code = 200
        self.report_periodicity = report_periodicity

    def json(self):
        return {
            'users': [
                {
                    "age": 42,
                    "email": "example@example.com",
                    "firstname": "Admin",
                    "id": 1,
                    "lastname": "Admin",
                    "max_hr": 180,
                    "rest_hr": 50,
                    "vo2max": 63.0,
                    "weight": 60.0,
                    "report_periodicity": self.report_periodicity
                }
            ]
        }

    def __call__(self):
        return self


# Credit to Edoardo, a borgataro before a man:
def correct_format_date(year=2025, month=2, day=1):
    return int(datetime.strptime(str(year) + '-' + str(month) + '-' + str(day), '%Y-%m-%d').timestamp())


class FakeRunsResponse:
    def __init__(self):
        self.status_code = 200

    def json(self):
        return [
            {
                "id": 1,
                "title": "Run1",
                "description": "Run1Description",
                "strava_id": 0,
                "distance": 1000,
                "start_date": correct_format_date(year=2011),
                "elapsed_time": 10,
                "average_speed": 10,
                "total_elevation_gain": 10
            }
        ]


def switchFakesDaily(x, *args, **kwargs):
    if 'run' in x:
        return FakeRunsResponse()

    return FakeUserResponse('Daily')


def switchFakesWeekly(x, *args, **kwargs):
    if 'run' in x:
        return FakeRunsResponse()

    return FakeUserResponse('Weekly')


def switchFakesMonthly(x, *args, **kwargs):
    if 'run' in x:
        return FakeRunsResponse()

    return FakeUserResponse('Monthly')


# Test if the method for sending reports is indeed invoked
def test_send_mail_to_user_one_run():
    with mock.patch("emailer.mail_service.get_request_retry", side_effect=switchFakesDaily):
        with mock.patch('emailer.mail_service.smtplib.SMTP') as mockedMail:
            mailservice = MailService()
            mailservice.sendReports()
            # we have successfully sent an email
            assert mockedMail.call_count == 1

    with mock.patch("emailer.mail_service.get_request_retry", side_effect=switchFakesWeekly):
        with mock.patch('emailer.mail_service.datetime.datetime') as mockedToday:
            mockedToday.today.return_value.isoweekday.return_value = 1

            with mock.patch('emailer.mail_service.smtplib.SMTP') as mockedMail:
                mailservice = MailService()
                mailservice.sendReports()
                # we have successfully sent an email
                assert mockedMail.call_count == 1

    with mock.patch("emailer.mail_service.get_request_retry", side_effect=switchFakesMonthly):
        with mock.patch('emailer.mail_service.datetime.datetime') as mockedToday:
            mockedToday.today.return_value.day.return_value = 1

            with mock.patch('emailer.mail_service.smtplib.SMTP') as mockedMail:
                mailservice = MailService()
                mailservice.sendReports()
                # we have successfully sent an email
                assert mockedMail.call_count == 1


# and now actually send the email, shall we?
def test_send_mail_dataservice_down():
    with mock.patch('emailer.mail_service.get_request_retry', side_effect=Exception):
        mailservice = MailService()
        with pytest.raises(Exception):
            mailservice.sendReports()
