from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Certificate

# Create your views here.
@login_required
def certificate_list(request):
    certs = Certificate.objects.filter(user=request.user)
    return render(request, 'certificate/certificate_list.html', {
        'certs': certs
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