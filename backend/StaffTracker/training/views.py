from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from .models import Training, TrainingRegistration
from department.models import Department
from django.contrib.auth.models import User
from django.utils.dateparse import parse_date
from datetime import datetime

# ---------------- HR ----------------
def is_hr(user):
    return user.groups.filter(name='HR').exists() or user.is_superuser

@login_required
@user_passes_test(is_hr)
def hr_dashboard(request):
    trainings = Training.objects.all()
    departments = Department.objects.all()
    trainers = User.objects.filter(groups__name='Trainer')

    dept_id = request.GET.get('department')
    trainer_id = request.GET.get('trainer')
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')

    if dept_id and dept_id != "":
        trainings = trainings.filter(department_id=dept_id)

    if trainer_id and trainer_id != "":
        trainings = trainings.filter(trainer_id=trainer_id)

    if start_date:
        trainings = trainings.filter(date__gte=start_date)
    if end_date:
        trainings = trainings.filter(date__lte=end_date)

    return render(request, 'training/hr_training_dashboard.html', {
        'trainings': trainings,
        'departments': departments,
        'trainers': trainers,
        'selected_department': dept_id,
        'selected_trainer': trainer_id,
        'start_date': start_date,
        'end_date': end_date
    })

@login_required
@user_passes_test(is_hr)
def hr_create_training(request):
    from django.contrib.auth.models import User
    from department.models import Department

    trainers = User.objects.filter(groups__name='Trainer')
    departments = Department.objects.all()

    if request.method == 'POST':
        title = request.POST.get('title')
        description = request.POST.get('description')
        date_str = request.POST.get('date')
        time_str = request.POST.get('time')
        location = request.POST.get('location')

        # CPD Points 非负
        cpd_points = request.POST.get('cpd_points', 0)
        try:
            cpd_points = max(0, int(cpd_points))
        except ValueError:
            cpd_points = 0

        # Duration 非负
        duration_hours = request.POST.get('duration_hours', 1)
        try:
            duration_hours = max(1, int(duration_hours))
        except ValueError:
            duration_hours = 1

        # Trainer
        trainer_user = None
        trainer_id = request.POST.get('trainer_id')
        if trainer_id:
            try:
                trainer_user = User.objects.get(id=trainer_id)
            except User.DoesNotExist:
                trainer_user = None

        # Department
        dept_id = request.POST.get('department_id')
        department = None
        if dept_id:
            try:
                department = Department.objects.get(id=dept_id)
            except Department.DoesNotExist:
                department = None

        from datetime import datetime
        date_val = datetime.strptime(date_str, '%Y-%m-%d').date() if date_str else None
        time_val = datetime.strptime(time_str, '%H:%M').time() if time_str else None

        Training.objects.create(
            title=title,
            description=description,
            date=date_val,
            time=time_val,
            location=location,
            trainer=trainer_user,
            cpd_points=cpd_points,
            duration_hours=duration_hours,
            department=department
        )

        messages.success(request, "Training created successfully")
        return redirect('hr_dashboard')

    return render(request, 'training/hr_create_training.html', {'trainers': trainers, 'departments': departments})

@login_required
@user_passes_test(is_hr)
def hr_edit_training(request, training_id):
    from django.contrib.auth.models import User
    from department.models import Department

    training = get_object_or_404(Training, id=training_id)
    trainers = User.objects.filter(groups__name='Trainer')
    departments = Department.objects.all()

    if request.method == 'POST':
        training.title = request.POST.get('title')
        training.description = request.POST.get('description')
        training.location = request.POST.get('location')

        cpd_points = request.POST.get('cpd_points')
        try:
            training.cpd_points = max(0, int(cpd_points))
        except (TypeError, ValueError):
            training.cpd_points = 0

        duration_hours = request.POST.get('duration_hours')
        try:
            training.duration_hours = max(1, int(duration_hours))
        except (TypeError, ValueError):
            training.duration_hours = 1

        trainer_id = request.POST.get('trainer_id')
        if trainer_id:
            try:
                training.trainer = User.objects.get(id=trainer_id)
            except User.DoesNotExist:
                training.trainer = None

        dept_id = request.POST.get('department_id')
        if dept_id:
            try:
                training.department = Department.objects.get(id=dept_id)
            except Department.DoesNotExist:
                training.department = None

        from datetime import datetime
        date_str = request.POST.get('date')
        time_str = request.POST.get('time')
        if date_str:
            training.date = datetime.strptime(date_str, '%Y-%m-%d').date()
        if time_str:
            training.time = datetime.strptime(time_str, '%H:%M').time()

        training.save()
        messages.success(request, "Training updated successfully")
        return redirect('hr_dashboard')

    return render(request, 'training/hr_edit_training.html', {
        'training': training,
        'trainers': trainers,
        'departments': departments
    })

@login_required
@user_passes_test(is_hr)
def hr_delete_training(request, training_id):
    training = get_object_or_404(Training, id=training_id)
    if request.method == 'POST':
        training.delete()
        messages.success(request, "Training deleted successfully")
        return redirect('hr_dashboard')
    return render(request, 'training/hr_delete_training.html', {'training': training})

@login_required
def hr_approve_registration(request, reg_id):
    reg = get_object_or_404(TrainingRegistration, id=reg_id)
    reg.status = 'Approved'
    reg.save()
    messages.success(request, f"{reg.employee.username}'s registration approved.")
    return redirect('hr_dashboard')

@login_required
def hr_reject_registration(request, reg_id):
    reg = get_object_or_404(TrainingRegistration, id=reg_id)
    reg.status = 'Rejected'
    reg.save()
    messages.warning(request, f"{reg.employee.username}'s registration rejected.")
    return redirect('hr_dashboard')

# ---------------- Trainer ----------------
@login_required
def trainer_dashboard(request):
    trainings = Training.objects.filter(trainer=request.user).order_by('date')
    departments = Department.objects.all()

    selected_department = request.GET.get('department')
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')

    if selected_department:
        trainings = trainings.filter(department_id=selected_department)

    if start_date:
        start_date_parsed = parse_date(start_date)
        if start_date_parsed:
            trainings = trainings.filter(date__gte=start_date_parsed)

    if end_date:
        end_date_parsed = parse_date(end_date)
        if end_date_parsed:
            trainings = trainings.filter(date__lte=end_date_parsed)

    context = {
        'trainings': trainings,
        'departments': departments,
        'selected_department': selected_department,
        'start_date': start_date,
        'end_date': end_date,
    }
    return render(request, 'training/training_dashboard.html', context)

@login_required
def create_training(request):
    from datetime import datetime
    from django.contrib.auth.models import User
    from .models import Training
    from department.models import Department

    if request.method == 'POST':
        title = request.POST.get('title')
        description = request.POST.get('description')
        date_str = request.POST.get('date')
        time_str = request.POST.get('time')
        location = request.POST.get('location')
        cpd_points = request.POST.get('cpd_points', 0)
        duration_hours = request.POST.get('duration_hours', 1)
        department_id = request.POST.get('department_id')

        try:
            cpd_points = max(int(cpd_points), 0)
        except ValueError:
            cpd_points = 0

        try:
            duration_hours = max(int(duration_hours), 1)
        except ValueError:
            duration_hours = 1

        training_date = datetime.strptime(date_str, '%Y-%m-%d').date() if date_str else None
        training_time = datetime.strptime(time_str, '%H:%M').time() if time_str else None
        department = Department.objects.get(id=department_id) if department_id else None

        Training.objects.create(
            title=title,
            description=description,
            date=training_date,
            time=training_time,
            location=location,
            trainer=request.user,
            cpd_points=cpd_points,
            duration_hours=duration_hours,
            department=department
        )
        return redirect('trainer_dashboard')

    departments = Department.objects.all()
    return render(request, 'training/create_training.html', {'departments': departments})


@login_required
def edit_training(request, training_id):
    from datetime import datetime
    from department.models import Department

    training = get_object_or_404(Training, id=training_id)

    if request.method == 'POST':
        training.title = request.POST.get('title')
        training.description = request.POST.get('description')
        date_str = request.POST.get('date')
        time_str = request.POST.get('time')
        training.location = request.POST.get('location')

        cpd_points = request.POST.get('cpd_points')
        if cpd_points is not None:
            try:
                training.cpd_points = max(int(cpd_points), 0)
            except ValueError:
                training.cpd_points = 0

        duration_hours = request.POST.get('duration_hours')
        if duration_hours is not None:
            try:
                training.duration_hours = max(int(duration_hours), 1)
            except ValueError:
                training.duration_hours = 1

        department_id = request.POST.get('department_id')
        if department_id:
            try:
                training.department = Department.objects.get(id=department_id)
            except Department.DoesNotExist:
                training.department = None
        else:
            training.department = None

        if date_str:
            training.date = datetime.strptime(date_str, '%Y-%m-%d').date()
        if time_str:
            training.time = datetime.strptime(time_str, '%H:%M').time()

        training.save()
        messages.success(request, "Training updated successfully")
        return redirect('trainer_dashboard')

    departments = Department.objects.all()
    return render(request, 'training/edit_training.html', {'training': training, 'departments': departments})

@login_required
def delete_training(request, training_id):
    training = get_object_or_404(Training, id=training_id, trainer=request.user)
    if request.method == 'POST':
        training.delete()
        return redirect('trainer_dashboard')
    return render(request, 'training/delete_training.html', {'training': training})


@login_required
@user_passes_test(is_hr)
def hr_training_registrations(request):
    registrations = TrainingRegistration.objects.select_related('employee', 'training').all()

    if request.method == 'POST':
        reg_id = request.POST.get('delete_id')
        if reg_id:
            reg = get_object_or_404(TrainingRegistration, id=reg_id)
            reg.delete()
            messages.success(request, "Registration deleted successfully.")
            return redirect('hr_training_registrations')

    return render(request, 'training/employee_registrations.html', {
        'registrations': registrations
    })

# ---------------- Employee ----------------

@login_required
def employee_dashboard(request):
    user = request.user

    # 获取 user profile 和 department
    user_profile = getattr(user, 'userprofile', None)
    user_department = user_profile.department if user_profile else None

    # 获取过滤日期
    start_date_str = request.GET.get('start_date')
    end_date_str = request.GET.get('end_date')

    # trainings queryset
    trainings = Training.objects.all()
    if user_department:
        trainings = trainings.filter(department=user_department)

    # 日期过滤
    start_date = None
    end_date = None
    if start_date_str:
        try:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            trainings = trainings.filter(date__gte=start_date)
        except ValueError:
            start_date = None

    if end_date_str:
        try:
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
            trainings = trainings.filter(date__lte=end_date)
        except ValueError:
            end_date = None

    # 获取该员工报名情况
    registrations = TrainingRegistration.objects.filter(employee=user)

    context = {
        'trainings': trainings,
        'registrations': registrations,
        'start_date': start_date_str,
        'end_date': end_date_str,
        'user_department': user_department,
    }

    return render(request, 'training/employee_list.html', context)

@login_required
def register_training(request, training_id):
    training = get_object_or_404(Training, id=training_id)

    if TrainingRegistration.objects.filter(employee=request.user, training=training).exists():
        messages.warning(request, "You have already registered for this training.")
    else:
        TrainingRegistration.objects.create(employee=request.user, training=training)
        messages.success(request, "Registration successful!")

    return redirect('employee_dashboard')

# ---------------- HOD ----------------
@login_required
def hod_dashboard(request):
    pending_regs = TrainingRegistration.objects.filter(status='Pending')
    return render(request, 'training/approval_list.html', {'pending_regs': pending_regs})

@login_required
def approve_registration(request, reg_id):
    reg = get_object_or_404(TrainingRegistration, id=reg_id)
    reg.status = 'Approved'
    reg.save()
    messages.success(request, f"{reg.employee.username}'s registration approved.")
    return redirect('hod_dashboard')

@login_required
def reject_registration(request, reg_id):
    reg = get_object_or_404(TrainingRegistration, id=reg_id)
    reg.status = 'Rejected'
    reg.save()
    messages.warning(request, f"{reg.employee.username}'s registration rejected.")
    return redirect('hod_dashboard')
