from datetime import date
from django.core.cache import cache
from certificate.utils import send_certificate_reminders

class CertificateReminderMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if hasattr(request, 'user') and request.user.is_authenticated:
            today = date.today().isoformat()
            key = f"cert_reminder_{today}"

            if not cache.get(key):
                send_certificate_reminders()
                cache.set(key, True, 86400)

        return self.get_response(request)