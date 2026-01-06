from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from .models import Certificate
from datetime import date

# Create your views here.
@login_required
def certificate_list(request):
    certs = Certificate.objects.filter(user=request.user)
    return render(request, 'certificate/certificate_list.html', {
        'certs': certs,
        'today': date.today(),
    })

@login_required
def issued_certificates(request):
    certs = Certificate.objects.all()
    return render(request, 'certificate/issued_certificates.html', {
        'certs': certs
    })

@login_required
def certificate_preview(request, pk):
    cert = get_object_or_404(Certificate, pk=pk)
    return render(request, 'certificate/certificate_preview.html', {
        'cert': cert
    })

def is_hr(user):
    return user.groups.filter(name='HR').exists() or user.is_superuser

@login_required
@user_passes_test(is_hr)
def hr_delete_certificate(request, cert_id):
    cert = get_object_or_404(Certificate, id=cert_id)
    if request.method == 'POST':
        cert.delete()
    return redirect('hr_dashboard')