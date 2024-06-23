from twilio.rest import Client
from django.conf import settings

def is_phone_number_verified(phone_number):
    client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
    incoming_phone_numbers = client.outgoing_caller_ids.list()

    for number in incoming_phone_numbers:
        print(number.phone_number)
        if number.phone_number == phone_number:
            return True
    return False

def send_verification_code(phone_number, channel='sms'):
    client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
    verification = client.verify.services(settings.TWILIO_VERIFY_SERVICE_SID).verifications.create(
        to=phone_number,
        channel=channel
    )
    return verification

def check_verification_code(phone_number, code):
    client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
    verification_check = client.verify.services(settings.TWILIO_VERIFY_SERVICE_SID).verification_checks.create(
        to=phone_number,
        code=code
    )
    return verification_check.status == 'approved'
