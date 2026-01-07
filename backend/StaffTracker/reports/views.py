from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from datetime import date, timedelta

from certificate.models import Certificate
from cpd.models import CPDRecord
from attendance.models import Attendance
from accounts.models import UserProfile
from department.models import Department
from training.models import Training

@login_required
def reports_dashboard(request):
    return render(request, 'reports/dashboard.html')


def hr_certificate_report(request):
    certificates = Certificate.objects.select_related(
        'user',
        'trainer',
        'training',
        'user__userprofile',      # User → UserProfile
        'trainer__userprofile',   # Trainer → UserProfile
        'training__department',
    )

    department_id = request.GET.get('department')
    trainer_id = request.GET.get('trainer')
    status = request.GET.get('status')

    if department_id:
        certificates = certificates.filter(
            user__userprofile__department_id=department_id
        )

    if trainer_id:
        certificates = certificates.filter(trainer_id=trainer_id)

    today = date.today()
    if status == 'valid':
        certificates = certificates.filter(expiry_date__gte=today)
    elif status == 'expired':
        certificates = certificates.filter(expiry_date__lt=today)

    context = {
        'certificates': certificates,
        'departments': Department.objects.all(),
        'trainers': UserProfile.objects.filter(role='Trainer'),
    }

    return render(request, 'reports/hr_certificate_report.html', context)

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

@login_required
def hod_department_training_progress(request):
    profile = request.user.userprofile
    department = profile.department

    employees = UserProfile.objects.filter(department=department)
    user_ids = [e.user.id for e in employees]  
    attendances = Attendance.objects.filter(user_id__in=user_ids)

    trainings_dict = {str(t.id): t for t in Training.objects.all()}

    for a in attendances:
        a.training_obj = trainings_dict.get(str(a.training_id))

    return render(request, 'reports/department_training_progress.html', {
        'department': department,
        'attendances': attendances
    })

@login_required
def hod_department_report(request):
    profile = request.user.userprofile
    department = profile.department

    if not department:
        return render(request, 'reports/department_report.html', {
            'department': None,
            'records': [],
            'total_cpd': 0,
        })

    employees = UserProfile.objects.filter(department=department)

    cpd_records = CPDRecord.objects.filter(
        user__in=[e.user for e in employees]
    )

    total_cpd = sum(r.points for r in cpd_records)

    return render(request, 'reports/department_report.html', {
        'department': department,
        'records': cpd_records,
        'total_cpd': total_cpd
    })