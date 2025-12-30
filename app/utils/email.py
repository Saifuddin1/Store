from flask_mail import Message
from app import mail


def send_email(subject, recipients, body):
    msg = Message(
        subject=subject,
        sender="rajusaifuddinrs1@gmail.com",
        recipients=recipients,
        body=body
    )
    mail.send(msg)
