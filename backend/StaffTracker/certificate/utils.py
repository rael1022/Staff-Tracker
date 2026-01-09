from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from .models import Certificate

def send_certificate_reminders():
    today = timezone.now().date()
    certs = Certificate.objects.select_related('user', 'training')

    for cert in certs:
        if not cert.user.email:
            continue

        days_left = (cert.expiry_date - today).days

        try:
            # ===== Expiry soon (7~1 days) =====
            if 1 <= days_left <= 7 and not cert.reminder_soon_sent:
                send_mail(
                    subject="Expiry Soon: ⏰ Certificate Expiry Reminder",
                    message=f"""
Dear {cert.user.get_full_name() or cert.user.username},

This is a formal reminder that your certificate for "{cert.training.title}" is due to expire on {cert.expiry_date} (in {days_left} day(s)).

We kindly request you to take the necessary action to renew it before the expiration date to ensure continued compliance.

Thank you for your prompt attention.

Best regards,
Staff Training & Certificate Tracker
""",
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[cert.user.email],
                )
                cert.reminder_soon_sent = True
                cert.save(update_fields=['reminder_soon_sent'])

            # ===== Expired =====
            elif days_left <= 0 and not cert.reminder_expired_sent:
                send_mail(
                    subject="Expired: 🛑 Certificate Expired",
                    message=f"""
Dear {cert.user.get_full_name() or cert.user.username},

We would like to inform you that your certificate for "{cert.training.title}" has expired on {cert.expiry_date}.

Please proceed to renew it at the earliest opportunity, or contact HR/Trainer for assistance.

Thank you for your attention.

Best regards,
Staff Training & Certificate Tracker
""",
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[cert.user.email],
                )
                cert.reminder_expired_sent = True
                cert.save(update_fields=['reminder_expired_sent'])

        except Exception as e:
            # 🚨 prevent login boom
            print("Email sending failed:", e)