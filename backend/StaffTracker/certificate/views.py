from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from .models import Certificate
from datetime import date
from django.contrib import messages
from django.contrib.auth.models import User
from training.models import Training, TrainingRegistration
from attendance.models import Attendance

# ====== Employee Views ======
@login_required
def certificate_list(request):
    """Employee view: list their own certificates"""
    certs = Certificate.objects.filter(user=request.user)
    return render(request, 'certificate/certificate_list.html', {
        'certs': certs,
        'today': date.today(),
    })


# ====== Trainer Views ======
@login_required
def trainer_certificates_dashboard(request):
    """Trainer dashboard: show only employees with attendance, merged trainings with filters"""
    if request.user.userprofile.role != 'Trainer':
        return redirect('dashboard')

    today = date.today()
    rows = []

    # ====== GET filters ======
    training_filter = request.GET.get('training')     # training.id
    employee_filter = request.GET.get('employee')     # username
    status_filter = request.GET.get('status')         # Active / Expired / Expiring Soon / Not Issued

    # ====== Trainer trainings ======
    trainings = Training.objects.filter(trainer=request.user).prefetch_related(
        'trainingregistration_set', 'certificate_set'
    )

    for training in trainings:

        # ====== Training filter ======
        if training_filter and str(training.id) != training_filter:
            continue

        # ====== Completed registrations ======
        completed_regs = training.trainingregistration_set.filter(
            complete_status='Completed'
        ).select_related('employee')

        # ====== Certificate map ======
        cert_map = {cert.user_id: cert for cert in training.certificate_set.all()}

        for reg in completed_regs:
            employee = reg.employee

            # ====== Attendance check ======
            attended = Attendance.objects.filter(
                user=employee,
                training_id=str(training.id),
                status=Attendance.Status.PRESENT
            ).exists()

            if not attended:
                continue  # 没出勤的员工不显示

            # ====== Employee name filter ======
            if employee_filter and employee_filter.lower() not in employee.username.lower():
                continue

            # ====== Get certificate ======
            cert = cert_map.get(employee.id)

            # ====== Certificate status calculation ======
            if cert:
                days_to_expiry = (cert.expiry_date - today).days
                if days_to_expiry < 0:
                    status = 'Expired'
                elif days_to_expiry <= 7:
                    status = 'Expiring Soon'
                else:
                    status = 'Active'
            else:
                status = 'Not Issued'

            # ====== Status filter ======
            if status_filter and status != status_filter:
                continue

            # ====== Append row ======
            rows.append({
                'training': training,
                'employee': employee,
                'cert': cert,
                'status': status
            })

    return render(request, 'certificate/issued_certificates.html', {
        'rows': rows,
        'trainings': trainings,
        'selected_training': training_filter,
        'selected_employee': employee_filter,
        'selected_status': status_filter,
    })


@login_required
def provide_certificate(request, training_id, user_id):
    """Trainer POST: provide certificate to an eligible employee"""
    if request.user.userprofile.role != 'Trainer':
        return redirect('dashboard')

    training = get_object_or_404(Training, id=training_id, trainer=request.user)
    employee = get_object_or_404(User, id=user_id)

    if Certificate.objects.filter(training=training, user=employee).exists():
        messages.warning(request, "Certificate already issued.")
        return redirect('trainer_certificates_dashboard')

    if request.method == 'POST':
        expiry_date = request.POST.get('expiry_date')
        if not expiry_date:
            messages.error(request, "Expiry date is required.")
            return redirect('trainer_certificates_dashboard')

        Certificate.objects.create(
            user=employee,
            training=training,
            trainer=request.user,
            expiry_date=expiry_date
        )
        messages.success(request, f"Certificate issued to {employee.username}.")
    return redirect('trainer_certificates_dashboard')


@login_required
def edit_certificate_expiry(request, cert_id):
    """Trainer POST: edit certificate expiry date"""
    if request.user.userprofile.role != 'Trainer':
        return redirect('dashboard')

    cert = get_object_or_404(Certificate, id=cert_id, trainer=request.user)

    if request.method == 'POST':
        expiry_date = request.POST.get('expiry_date')
        if not expiry_date:
            messages.error(request, "Expiry date is required.")
            return redirect('trainer_certificates_dashboard')

        cert.expiry_date = expiry_date
        cert.save()
        messages.success(request, f"Expiry date updated for {cert.user.username}.")
    return redirect('trainer_certificates_dashboard')


@login_required
def issued_certificates(request):
    """Trainer view: list all issued certificates with days_to_expiry for template"""
    if request.user.userprofile.role != 'Trainer':
        return redirect('dashboard')

    certs = Certificate.objects.filter(trainer=request.user)
    today = date.today()

    for cert in certs:
        cert.days_to_expiry = (cert.expiry_date - today).days

    return render(request, 'certificate/issued_certificates.html', {
        'certs': certs,
        'today': today
    })


# ====== Certificate Preview (all roles) ======
@login_required
def certificate_preview(request, pk):
    """Preview certificate: Employee can see own, Trainer sees issued, HR sees all"""
    cert = get_object_or_404(Certificate, pk=pk)

    # Permission check
    user_role = getattr(request.user, 'userprofile', None)
    if cert.user != request.user and cert.trainer != request.user and not (user_role and user_role.role == 'HR'):
        messages.error(request, "You do not have permission to view this certificate.")
        return redirect('dashboard')

    return render(request, 'certificate/certificate_preview.html', {
        'cert': cert
    })


# ====== HR Views ======
def is_hr(user):
    return user.groups.filter(name='HR').exists() or user.is_superuser


@login_required
@user_passes_test(is_hr)
def hr_delete_certificate(request, cert_id):
    """HR: delete certificate"""
    cert = get_object_or_404(Certificate, id=cert_id)
    if request.method == 'POST':
        cert.delete()
        messages.success(request, "Certificate deleted successfully.")
    return redirect('hr_dashboard')

@login_required
def print_certificate(request, cert_id):
    cert = get_object_or_404(Certificate, id=cert_id)
    context = {'cert': cert}
    return render(request, 'certificate/print_certificate.html', context)
