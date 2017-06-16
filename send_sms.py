from secret import TWILIO_AUTH_TOKEN, TWILIO_ACCOUNT_SID, TWILIO_PHONE, MY_PHONE_NUMBER
from twilio.rest import Client


def send_SMS(message):
    auth_token = TWILIO_AUTH_TOKEN
    account_sid = TWILIO_ACCOUNT_SID
    client = Client(account_sid, auth_token)

    message = client.messages.create(
        to=MY_PHONE_NUMBER,
        from_=TWILIO_PHONE,
        body=message)
    return message.sid

if __name__ == '__main__':

    print(send_SMS())
