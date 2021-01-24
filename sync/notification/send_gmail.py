from __future__ import print_function
import os.path
from email.mime.text import MIMEText
import base64
import logging
from sync.appconfig import EMAIL_FROM, EMAIL_TO
from sync.security.auth import get_service

logging_format = "%(asctime)s (%(levelname)s): %(message)s"
logging.basicConfig(level=logging.INFO, format=logging_format)
 




def authorize():
    PATH = os.chdir(os.path.dirname(os.path.abspath( __file__ )))
    return get_service(
        path=os.path.dirname(os.path.abspath(__file__)),
        scope="https://mail.google.com/",
        build_name="gmail", 
        build_version="v1"
    )


def send_message(service, user_id, message):
    """Send an email message.

    Args:
    service: Authorized Gmail API service instance.
    user_id: User's email address. The special value "me"
    can be used to indicate the authenticated user.
    message: Message to be sent.

    Returns:
    Sent Message.
    """
    service.users().messages().send(userId=user_id, body=message).execute()


def create_message(sender, to, subject, message_text):
    """Create a message for an email.

    Args:
    sender: Email address of the sender.
    to: Email address of the receiver.
    subject: The subject of the email message.
    message_text: The text of the email message.

    Returns:
    An object containing a base64url encoded email object.
    """
    message = MIMEText(message_text)
    message["to"] = to
    message["from"] = sender
    message["subject"] = subject
    raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
    # raw = raw.decode()
    return {"raw": raw}


def notify(message):
    msg = create_message(
        EMAIL_FROM, EMAIL_TO, "Google Calendar API - Data error", message
    )
    service = authorize()
    send_message(service=service, user_id="me", message=msg)


if __name__ == "__main__":
    notify("test")
