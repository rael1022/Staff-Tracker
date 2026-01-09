from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from datetime import date, timedelta

from certificate.models import Certificate
from cpd.models import CPDRecord
from attendance.models import Attendance
from accounts.models import UserProfile
from department.models import Department
from training.models import Training, TrainingRegistration
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
    records = CPDRecord.objects.select_related(
        'user',
        'training',
        'user__userprofile',
        'training__department',
    )

    # filters
    department_id = request.GET.get('department')
    employee_name = request.GET.get('employee')
    training_name = request.GET.get('training')
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')

    if department_id:
        records = records.filter(
            user__userprofile__department_id=department_id
        )

    if employee_name:
        records = records.filter(
            user__username__icontains=employee_name
        )

    if training_name:
        records = records.filter(
            training__title__icontains=training_name
        )

    if start_date:
        records = records.filter(earned_date__gte=start_date)

    if end_date:
        records = records.filter(earned_date__lte=end_date)

    total_points = records.aggregate(
        total=models.Sum('points')
    )['total'] or 0

    context = {
        'records': records,
        'departments': Department.objects.all(),
        'total_points': total_points,

        # keep filters
        'selected_department': int(department_id) if department_id else '',
        'selected_employee': employee_name or '',
        'selected_training': training_name or '',
        'start_date': start_date or '',
        'end_date': end_date or '',
    }

    return render(request, 'reports/cpd_summary.html', context)


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

    employee_name = request.GET.get('employee', '').strip()
    training_name = request.GET.get('training', '').strip()
    completion_status = request.GET.get('status', '')
    certificate_filter = request.GET.get('certificate', '')

    employees = UserProfile.objects.filter(department=department)
    if employee_name:
        employees = employees.filter(user__username__icontains=employee_name)
    user_ids = employees.values_list('user_id', flat=True)

    registrations = TrainingRegistration.objects.filter(employee_id__in=user_ids)\
        .select_related('employee', 'training')

    if training_name:
        registrations = registrations.filter(training__title__icontains=training_name)

    if completion_status in ['Completed', 'Not Completed']:
        registrations = registrations.filter(complete_status=completion_status)

    attendance_qs = Attendance.objects.filter(user_id__in=user_ids)
    attendance_map = {(att.user_id, att.training_id): att.status for att in attendance_qs}

    certificates = Certificate.objects.filter(user_id__in=user_ids)
    cert_map = {(c.user_id, str(c.training.id)): c for c in certificates}

    cpd_qs = CPDRecord.objects.filter(user_id__in=user_ids)
    cpd_map = {}
    for r in cpd_qs:
        key = (r.user_id, str(r.training.id))
        cpd_map[key] = cpd_map.get(key, 0) + r.points

    today = date.today()

    filtered_regs = []
    for r in registrations:
        training_id_str = str(r.training.id)
        r.attendance_status = attendance_map.get((r.employee.id, training_id_str), '-')
        r.certificate = cert_map.get((r.employee.id, training_id_str))
        r.cpd_points = cpd_map.get((r.employee.id, training_id_str), 0)

        if certificate_filter == 'Active':
            if not r.certificate or r.certificate.expiry_date < today:
                continue
        elif certificate_filter == 'Expired':
            if not r.certificate or r.certificate.expiry_date >= today:
                continue

        filtered_regs.append(r)

    context = {
        'department': department,
        'registrations': filtered_regs,
        'selected_employee': employee_name,
        'selected_training': training_name,
        'selected_status': completion_status,
        'selected_certificate': certificate_filter,
        'today': today,
    }

    return render(request, 'reports/department_training_progress.html', context)



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

@login_required
def cpd_summary_download(request):
    records = CPDRecord.objects.select_related(
        'user',
        'training',
        'user__userprofile',
        'training__department',
    )

    department_id = request.GET.get('department')
    employee_name = request.GET.get('employee')
    training_name = request.GET.get('training')
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')

    if department_id:
        records = records.filter(user__userprofile__department_id=department_id)
    if employee_name:
        records = records.filter(user__username__icontains=employee_name)
    if training_name:
        records = records.filter(training__title__icontains=training_name)
    if start_date:
        records = records.filter(earned_date__gte=start_date)
    if end_date:
        records = records.filter(earned_date__lte=end_date)

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="cpd_summary.csv"'

    writer = csv.writer(response)
    writer.writerow(['Employee', 'Department', 'Training', 'CPD Points', 'Date'])

    for r in records:
        writer.writerow([
            r.user.username,
            r.user.userprofile.department.name if r.user.userprofile.department else '-',
            r.training.title if r.training else '-',
            r.points,
            r.earned_date
        ])

    return response