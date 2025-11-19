# whatsapp.py
import os, requests
import logging
from twilio.rest import Client
from testing import WHATSAPP_PROVIDER as b
from testing import TWILIO_AUTH_TOKEN as c
from testing import TWILIO_ACCOUNT_SID as d
from testing import TWILIO_WHATSAPP_FROM as e
import re

from typing import Optional, Dict, Any
from twilio.base.exceptions import TwilioRestException

# Provider flag (if you use it elsewhere)
PROVIDER = b

# Use testing.py values exactly as imported
TW_ACCOUNT_SID = d
TW_AUTH_TOKEN = c
TW_WHATSAPP_FROM = e

# --------------------------
#  Twilio Client (lazy load)
# --------------------------
_twilio_client: Optional[Client] = None

def get_twilio_client() -> Client:
    global _twilio_client
    if _twilio_client is None:
        if not TW_ACCOUNT_SID or not TW_AUTH_TOKEN:
            raise RuntimeError("Twilio credentials missing. Check testing.py")
        _twilio_client = Client(TW_ACCOUNT_SID, TW_AUTH_TOKEN)
    return _twilio_client


# --------------------------
#  PHONE NORMALIZATION
# --------------------------
def normalize_phone_number(number: str, default_country_code: str = "+91") -> str:
    """
    Convert user phone numbers into +91xxxx format (without whatsapp: prefix).
    Accepts:
      - '7499591914'
      - '+917499591914'
      - 'whatsapp:+917499591914'
    """
    if not number:
        raise ValueError("Phone number is empty")

    number = str(number).strip()

    # remove whitespace & characters
    number = re.sub(r"[ \-\(\)]", "", number)

    # strip `whatsapp:` prefix
    if number.startswith("whatsapp:"):
        number = number.split(":", 1)[1]

    # already international
    if number.startswith("+"):
        return number

    # remove leading zeros
    number = number.lstrip("0")

    # add +91 by default
    return f"{default_country_code}{number}"


def ensure_whatsapp_prefix(number: str) -> str:
    """
    Ensures Twilio-friendly format: whatsapp:+91xxxxxx
    """
    if number.startswith("whatsapp:"):
        return number
    if not number.startswith("+"):
        raise ValueError("Phone number must start with + before adding whatsapp: prefix")
    return f"whatsapp:{number}"


# --------------------------
#  SEND MESSAGE
# --------------------------
def send_whatsapp(number: str, text: str, normalize: bool = True) -> Dict[str, Any]:
    """
    Send WhatsApp message through Twilio.
    Returns: { sid, status, to } or { error: ... }
    """
    try:
        # 1. normalize phone
        if normalize:
            normalized = normalize_phone_number(number)
        else:
            normalized = number

        # 2. ensure whatsapp:+ prefix
        to = ensure_whatsapp_prefix(normalized)

        # 3. Twilio client
        client = get_twilio_client()

        # 4. Send message
        msg = client.messages.create(
            from_=TW_WHATSAPP_FROM,
            body=str(text),
            to=to
        )

        logging.info(f"WhatsApp -> {to}, SID={msg.sid}, status={msg.status}")
        return {
            "sid": msg.sid,
            "status": msg.status,
            "to": to
        }

    except TwilioRestException as tex:
        logging.error(f"TwilioRestException: {tex}")
        return {"error": str(tex), "code": getattr(tex, "code", None)}

    except Exception as e:
        logging.error(f"General WhatsApp send error: {e}")
        return {"error": str(e)}


# BACKWARD_COMPAT
def send_twilio(number: str, text: str) -> Dict[str, Any]:
    return send_whatsapp(number, text)
