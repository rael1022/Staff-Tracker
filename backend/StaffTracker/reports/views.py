from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from datetime import date, timedelta

from certificate.models import Certificate
from cpd.models import CPDRecord
from attendance.models import Attendance

@login_required
def reports_dashboard(request):
    return render(request, 'reports/dashboard.html')


@login_required
def certificate_expiry_report(request):
    soon = date.today() + timedelta(days=30)
    expiring = Certificate.objects.filter(expiry_date__lte=soon)

    return render(request, 'reports/certificate_expiry.html', {
        'expiring': expiring,
        'soon_date': soon,
    })


@login_required
def cpd_summary_report(request):
    records = CPDRecord.objects.all()
    total_points = sum(r.points for r in records)

    return render(request, 'reports/cpd_summary.html', {
        'records': records,
        'total_points': total_points,
    })


@login_required
def attendance_summary_report(request):
    records = Attendance.objects.all().order_by('-date', '-check_in_time')

    total = records.count()
    present = records.filter(status='Present').count()
    absent = records.filter(status='Absent').count()

    return render(request, 'reports/attendance_summary.html', {
        'records': records,
        'total': total,
        'present': present,
        'absent': absent,
    })