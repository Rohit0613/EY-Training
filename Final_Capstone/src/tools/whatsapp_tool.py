import os
from dotenv import load_dotenv
load_dotenv()
from twilio.rest import Client


TWILIO_ACCOUNT_SID = os.getenv('TWILIO_ACCOUNT_SID')
TWILIO_AUTH_TOKEN = os.getenv('TWILIO_AUTH_TOKEN')
TWILIO_WHATSAPP_FROM = os.getenv('TWILIO_WHATSAPP_FROM')


class WhatsAppTool:
    def __init__(self):
        if TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN and TWILIO_WHATSAPP_FROM:
            self.client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        else:
            self.client = None


    def send(self, to_number: str, body: str):
        if not self.client:
            print('[WhatsApp Stub] TO:', to_number, '', body)
            return {'status': 'stubbed', 'body': body}
        msg = self.client.messages.create(
        body=body,
        from_=TWILIO_WHATSAPP_FROM,
        to=to_number
        )
        return {'sid': msg.sid}