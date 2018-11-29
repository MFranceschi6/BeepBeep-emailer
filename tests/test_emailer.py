import pytest
from unittest import mock
from datetime import datetime


from emailer.mail_service import *


#Test if the method for sending reports is indeed invoked
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
                "report_periodicity" : "No"
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

        with mock.patch('monolith.mail_service.smtplib.SMTP') as mockedMail:
            mailservice = MailService()
            mailservice.sendReports()
            #we have successfully sent an email
            assert mockedMail.call_count == 1


#Test if the method for sending reports is indeed invoked
def test_send_mail_to_user_one_run():
    with mock.patch("emailer.mail_service.get_request_retry") as mockedUser:
        mockedUser.return_value.status_code = 200
        mockedUser.return_value.json.return_value = {
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
                "report_periodicity" : "Daily"
            }
        ]}






            #and now actually send the email, shall we?






#def test_send_mail_dataservice_down():
 #   mailservice = MailService()

  #  with pytest.raises(Exception):
   #     mailservice.sendReports()



#Credits to Edoardo:




