from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from datetime import date, timedelta

from certificate.models import Certificate
from cpd.models import CPDRecord
from attendance.models import Attendance
from accounts.models import UserProfile
from department.models import Department
from training.models import Training
from django.db import models
import csv
from django.http import HttpResponse

@login_required
def reports_dashboard(request):
    return render(request, 'reports/dashboard.html')


def hr_certificate_report(request):
    certificates = Certificate.objects.select_related(
        'user',
        'trainer',
        'training',
        'user__userprofile',
        'trainer__userprofile', 
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


from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from attendance.models import Attendance
from accounts.models import UserProfile
from department.models import Department
from training.models import Training

@login_required
def attendance_summary_report(request):
    records = Attendance.objects.select_related('user')

    department_id = request.GET.get('department')
    training_name = request.GET.get('training')
    status = request.GET.get('status')

    if department_id:
        records = records.filter(user__userprofile__department_id=department_id)

    if training_name:
        matched_trainings = Training.objects.filter(title__icontains=training_name)
        matched_ids = matched_trainings.values_list('id', flat=True)
        records = records.filter(training_id__in=[str(tid) for tid in matched_ids])

    if status in ['Present', 'Absent']:
        records = records.filter(status=status)

    trainings = Training.objects.all()
    training_map = {str(t.id): t for t in trainings}
    for r in records:
        r.training_obj = training_map.get(r.training_id)
        r.department_name = (
            r.user.userprofile.department.name
            if r.user and r.user.userprofile.department
            else '-'
        )

    total = records.count()
    present = records.filter(status='Present').count()
    absent = records.filter(status='Absent').count()

    context = {
        'records': records,
        'total': total,
        'present': present,
        'absent': absent,
        'departments': Department.objects.all(),
        'trainings': trainings,
        'selected_department': int(department_id) if department_id else '',
        'selected_training': training_name or '',
        'selected_status': status or '',
    }

    return render(request, 'reports/attendance_summary.html', context)


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
            'department': None
        })

    employees = UserProfile.objects.filter(department=department)
    user_ids = employees.values_list('user_id', flat=True)

    attendance_total = Attendance.objects.filter(user_id__in=user_ids).count()
    present_count = Attendance.objects.filter(
        user_id__in=user_ids,
        status='Present'
    ).count()

    attendance_rate = 0
    if attendance_total > 0:
        attendance_rate = round((present_count / attendance_total) * 100, 1)

    total_cpd = CPDRecord.objects.filter(
        user_id__in=user_ids
    ).aggregate(total=models.Sum('points'))['total'] or 0

    return render(request, 'reports/department_report.html', {
        'department': department,
        'attendance_rate': attendance_rate,
        'total_cpd': total_cpd,
        'employee_count': employees.count()
    })


@login_required
def hod_department_cpdreport(request):
    profile = request.user.userprofile
    department = profile.department

    if not department:
        return render(request, 'reports/department_cpdreport.html', {
            'department': None,
            'records': [],
            'total_cpd': 0,
        })

    employees = UserProfile.objects.filter(department=department)

    cpd_records = CPDRecord.objects.filter(
        user__in=[e.user for e in employees]
    )

    total_cpd = sum(r.points for r in cpd_records)

    return render(request, 'reports/department_cpdreport.html', {
        'department': department,
        'records': cpd_records,
        'total_cpd': total_cpd
    })

@login_required
def hod_department_attendancereport(request):
    profile = request.user.userprofile
    department = profile.department

    employees = UserProfile.objects.filter(department=department)
    user_ids = [e.user.id for e in employees]  
    attendances = Attendance.objects.filter(user_id__in=user_ids)

    trainings_dict = {str(t.id): t for t in Training.objects.all()}

    for a in attendances:
        a.training_obj = trainings_dict.get(str(a.training_id))

    return render(request, 'reports/department_attendancereport.html', {
        'department': department,
        'attendances': attendances
    })

@login_required
def hod_department_attendance_download(request):
    profile = request.user.userprofile
    department = profile.department

    employees = UserProfile.objects.filter(department=department)
    user_ids = employees.values_list('user_id', flat=True)

    attendances = Attendance.objects.filter(user_id__in=user_ids)

    trainings_dict = {str(t.id): t for t in Training.objects.all()}
    for a in attendances:
        a.training_obj = trainings_dict.get(str(a.training_id))

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = (
        f'attachment; filename="{department.name}_attendance_report.csv"'
    )

    writer = csv.writer(response)
    writer.writerow(['Employee', 'Training', 'Status', 'Date'])

    for a in attendances:
        writer.writerow([
            a.user.username,
            a.training_obj.title if a.training_obj else '-',
            a.status,
            a.date
        ])

    return response

@login_required
def hod_department_cpd_download(request):
    profile = request.user.userprofile
    department = profile.department

    employees = UserProfile.objects.filter(department=department)
    users = [e.user for e in employees]

    cpd_records = CPDRecord.objects.filter(user__in=users)

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = (
        f'attachment; filename="{department.name}_cpd_report.csv"'
    )

    writer = csv.writer(response)
    writer.writerow(['Employee', 'Training', 'CPD Points'])

    for r in cpd_records:
        writer.writerow([
            r.user.username,
            r.training.title if r.training else '-',
            r.points
        ])

    return response