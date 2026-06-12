import smtplib
from dataclasses import dataclass
from email.message import EmailMessage
from urllib.parse import quote

from app.core.config import settings
from app.db import models
from app.services.calendar_email import format_ics_datetime


@dataclass
class EventInviteDelivery:
    delivery_status: str
    recipient_email: str | None
    subject: str
    body: str
    mailto_url: str
    ics_content: str


def build_event_invite(client: models.Client | None, scheduled: models.ScheduledEvent) -> EventInviteDelivery:
    organizer_email = settings.smtp_from_email or "coach@talon.local"
    recipient_email = client.email if client else (scheduled.attendees[0] if scheduled.attendees else None)
    recipient_name = client.full_name if client else "there"
    provider_name = {
        "google_meet": "Google Meet",
        "zoom": "Zoom",
        "teams": "Microsoft Teams",
    }.get(scheduled.meeting_provider, "Video meeting")
    meeting_link = scheduled.meeting_link or scheduled.google_meet_link or scheduled.location or "Online meeting"
    subject = f"Invitation: {scheduled.title}"
    description = (scheduled.description or "Coaching session").replace("\n", "\\n")
    body = (
        f"Hi {recipient_name},\n\n"
        f"You are scheduled for {scheduled.title}.\n\n"
        f"Date/time: {scheduled.start_time.strftime('%A, %B %d, %Y at %I:%M %p')}\n"
        f"Location: {provider_name}\n"
        f"Meeting link: {meeting_link}\n\n"
        f"Agenda / prep notes:\n{scheduled.description or 'We will align on goals, current priorities, and next steps.'}\n\n"
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
            f"UID:{scheduled.id}@talon.local",
            f"DTSTAMP:{format_ics_datetime(scheduled.created_at)}",
            f"DTSTART:{format_ics_datetime(scheduled.start_time)}",
            f"DTEND:{format_ics_datetime(scheduled.end_time)}",
            f"SUMMARY:{scheduled.title}",
            f"DESCRIPTION:{description}\\n\\nMeeting link: {meeting_link}",
            f"LOCATION:{meeting_link}",
            f"ORGANIZER;CN={settings.coach_display_name}:mailto:{organizer_email}",
            f"ATTENDEE;CN={recipient_name};ROLE=REQ-PARTICIPANT;PARTSTAT=NEEDS-ACTION;RSVP=TRUE:mailto:{recipient_email or ''}",
            "END:VEVENT",
            "END:VCALENDAR",
            "",
        ]
    )
    mailto = f"mailto:{quote(recipient_email or '')}?subject={quote(subject)}&body={quote(body)}"
    return EventInviteDelivery("drafted", recipient_email, subject, body, mailto, ics_content)


def send_event_invite(client: models.Client | None, scheduled: models.ScheduledEvent) -> EventInviteDelivery:
    invite = build_event_invite(client, scheduled)
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
