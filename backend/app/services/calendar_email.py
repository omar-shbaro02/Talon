import smtplib
from dataclasses import dataclass
from datetime import timedelta
from email.message import EmailMessage
from urllib.parse import quote

from app.core.config import settings
from app.db import models


@dataclass
class InviteDelivery:
    delivery_status: str
    recipient_email: str | None
    subject: str
    body: str
    mailto_url: str
    ics_content: str


def format_ics_datetime(value):
    return value.strftime("%Y%m%dT%H%M%SZ")


def build_invite(client: models.Client, session: models.Session) -> InviteDelivery:
    end_time = session.session_date + timedelta(minutes=session.duration_minutes)
    organizer_email = settings.smtp_from_email or "coach@talon.local"
    recipient_email = client.email
    subject = f"Invitation: {session.title}"
    location = session.location or "Online coaching session"
    description = (session.notes or "Coaching session").replace("\n", "\\n")
    body = (
        f"Hi {client.full_name},\n\n"
        f"You are scheduled for {session.title}.\n\n"
        f"Date/time: {session.session_date.strftime('%A, %B %d, %Y at %I:%M %p')}\n"
        f"Duration: {session.duration_minutes} minutes\n"
        f"Location: {location}\n\n"
        f"Agenda / prep notes:\n{session.notes or 'We will align on goals, current priorities, and next steps.'}\n\n"
        f"Best,\n{settings.coach_display_name}"
    )
    ics_content = "\r\n".join(
        [
            "BEGIN:VCALENDAR",
            "VERSION:2.0",
            "PRODID:-//TALON//Coaching Intelligence Platform//EN",
            "CALSCALE:GREGORIAN",
            "METHOD:REQUEST",
            "BEGIN:VEVENT",
            f"UID:{session.id}@talon.local",
            f"DTSTAMP:{format_ics_datetime(session.created_at)}",
            f"DTSTART:{format_ics_datetime(session.session_date)}",
            f"DTEND:{format_ics_datetime(end_time)}",
            f"SUMMARY:{session.title}",
            f"DESCRIPTION:{description}",
            f"LOCATION:{location}",
            f"ORGANIZER;CN={settings.coach_display_name}:mailto:{organizer_email}",
            f"ATTENDEE;CN={client.full_name};ROLE=REQ-PARTICIPANT;PARTSTAT=NEEDS-ACTION;RSVP=TRUE:mailto:{recipient_email or ''}",
            "END:VEVENT",
            "END:VCALENDAR",
            "",
        ]
    )
    mailto = f"mailto:{quote(recipient_email or '')}?subject={quote(subject)}&body={quote(body)}"
    return InviteDelivery(
        delivery_status="drafted",
        recipient_email=recipient_email,
        subject=subject,
        body=body,
        mailto_url=mailto,
        ics_content=ics_content,
    )


def send_session_invite(client: models.Client, session: models.Session) -> InviteDelivery:
    invite = build_invite(client, session)
    if not settings.email_enabled or not invite.recipient_email:
        return invite

    message = EmailMessage()
    message["Subject"] = invite.subject
    message["From"] = settings.smtp_from_email
    message["To"] = invite.recipient_email
    message.set_content(invite.body)
    message.add_attachment(
        invite.ics_content,
        subtype="calendar",
        filename="talon-session.ics",
        params={"method": "REQUEST"},
    )

    with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=20) as smtp:
        if settings.smtp_use_tls:
            smtp.starttls()
        if settings.smtp_username and settings.smtp_password:
            smtp.login(settings.smtp_username, settings.smtp_password)
        smtp.send_message(message)

    invite.delivery_status = "sent"
    return invite
