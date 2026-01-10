from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from .models import Training, TrainingRegistration
from department.models import Department
from django.contrib.auth.models import User
from django.utils.dateparse import parse_date
from django.utils import timezone
from datetime import datetime, timedelta
from attendance.models import Attendance
from django.contrib import messages
from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver

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
    from datetime import datetime
    from django.contrib import messages

    trainers = User.objects.filter(groups__name='Trainer')
    departments = Department.objects.all()

    if request.method == 'POST':
        title = request.POST.get('title')
        description = request.POST.get('description')
        date_str = request.POST.get('date')
        time_str = request.POST.get('time')
        location = request.POST.get('location')

        if Training.objects.filter(title__iexact=title).exists():
            messages.error(request, "Training with this title already exists.")
            return render(
                request,
                'training/hr_create_training.html',
                {'trainers': trainers, 'departments': departments}
            )

        cpd_points = request.POST.get('cpd_points', 0)
        try:
            cpd_points = max(0, int(cpd_points))
        except ValueError:
            cpd_points = 0

        duration_hours = request.POST.get('duration_hours', 1)
        try:
            duration_hours = max(1, int(duration_hours))
        except ValueError:
            duration_hours = 1

        trainer_user = None
        trainer_id = request.POST.get('trainer_id')
        if trainer_id:
            try:
                trainer_user = User.objects.get(id=trainer_id)
            except User.DoesNotExist:
                trainer_user = None

        department = None
        dept_id = request.POST.get('department_id')
        if dept_id:
            try:
                department = Department.objects.get(id=dept_id)
            except Department.DoesNotExist:
                department = None

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

    return render(
        request,
        'training/hr_create_training.html',
        {'trainers': trainers, 'departments': departments}
    )

@login_required
@user_passes_test(is_hr)
def hr_edit_training(request, training_id):
    from datetime import datetime
    from django.utils import timezone
    from django.contrib.auth.models import User
    from department.models import Department
    from django.contrib import messages

    training = get_object_or_404(Training, id=training_id)
    trainers = User.objects.filter(groups__name='Trainer')
    departments = Department.objects.all()

    if request.method == 'POST':
        old_date = training.date
        old_time = training.time
        old_duration = training.duration_hours
        
        new_title = request.POST.get('title')

        if Training.objects.filter(title__iexact=new_title).exclude(id=training.id).exists():
            messages.error(request, "Another training with this title already exists.")
            return render(request, 'training/hr_edit_training.html', {
                'training': training,
                'trainers': trainers,
                'departments': departments
            })

        training.title = new_title
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
        else:
            training.trainer = None

        dept_id = request.POST.get('department_id')
        if dept_id:
            try:
                training.department = Department.objects.get(id=dept_id)
            except Department.DoesNotExist:
                training.department = None
        else:
            training.department = None

        date_str = request.POST.get('date')
        time_str = request.POST.get('time')
        if date_str:
            try:
                training.date = datetime.strptime(date_str, '%Y-%m-%d').date()
            except ValueError:
                messages.error(request, "Invalid date format.")
                return redirect('hr_edit_training', training_id=training_id)
        if time_str:
            try:
                training.time = datetime.strptime(time_str, '%H:%M').time()
            except ValueError:
                messages.error(request, "Invalid time format.")
                return redirect('hr_edit_training', training_id=training_id)
        
        training.save()
        
        messages.success(request, "Training updated successfully.")  
        return redirect('hr_dashboard')

    current_time = timezone.now()
    current_end_time = datetime.combine(
        training.date, 
        training.time
    ).replace(tzinfo=current_time.tzinfo) + timedelta(hours=training.duration_hours)
    
    is_past_training = current_time > current_end_time
    approved_registrations_count = training.trainingregistration_set.filter(status='Approved').count()

    return render(request, 'training/hr_edit_training.html', {
        'training': training,
        'trainers': trainers,
        'departments': departments,
        'is_past_training': is_past_training,
        'approved_registrations_count': approved_registrations_count,
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
@user_passes_test(is_hr)
def hr_training_registrations(request):
    trainings = Training.objects.select_related(
        'trainer', 'department'
    ).prefetch_related(
        'trainingregistration_set__employee'
    )

    # ===== 获取筛选参数 =====
    trainer_id = request.GET.get('trainer')
    department_id = request.GET.get('department')

    if trainer_id:
        trainings = trainings.filter(trainer_id=trainer_id)

    if department_id:
        trainings = trainings.filter(department_id=department_id)

    # ===== 下拉选项数据 =====
    trainers = User.objects.filter(training__isnull=False).distinct()
    departments = Department.objects.all()

    return render(request, 'training/employee_registrations.html', {
        'trainings': trainings,
        'trainers': trainers,
        'departments': departments,
        'selected_trainer': trainer_id,
        'selected_department': department_id,
    })
    
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
    from django.contrib import messages
    from department.models import Department
    from .models import Training

    if request.method == 'POST':
        title = request.POST.get('title')
        description = request.POST.get('description')
        date_str = request.POST.get('date')
        time_str = request.POST.get('time')
        location = request.POST.get('location')
        cpd_points = request.POST.get('cpd_points', 0)
        duration_hours = request.POST.get('duration_hours', 1)
        department_id = request.POST.get('department_id')

        if Training.objects.filter(title__iexact=title).exists():
            messages.error(request, "Training with this title already exists.")
            departments = Department.objects.all()
            return render(
                request,
                'training/create_training.html',
                {'departments': departments}
            )

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

        messages.success(request, "Training created successfully.")
        return redirect('trainer_dashboard')

    departments = Department.objects.all()
    return render(request, 'training/create_training.html', {'departments': departments})

@login_required
def edit_training(request, training_id):
    from datetime import datetime
    from department.models import Department
    from django.contrib import messages

    training = get_object_or_404(Training, id=training_id)

    if request.method == 'POST':
        new_title = request.POST.get('title')

        if Training.objects.filter(title__iexact=new_title).exclude(id=training.id).exists():
            messages.error(request, "Another training with this title already exists.")
            departments = Department.objects.all()
            return render(request, 'training/edit_training.html', {
                'training': training,
                'departments': departments
            })

        training.title = new_title
        training.description = request.POST.get('description')

        date_str = request.POST.get('date')
        time_str = request.POST.get('time')
        training.location = request.POST.get('location')

        cpd_points = request.POST.get('cpd_points')
        try:
            training.cpd_points = max(int(cpd_points), 0)
        except (TypeError, ValueError):
            training.cpd_points = 0

        duration_hours = request.POST.get('duration_hours')
        try:
            training.duration_hours = max(int(duration_hours), 1)
        except (TypeError, ValueError):
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
    return render(request, 'training/edit_training.html', {
        'training': training,
        'departments': departments
    })

@login_required
def delete_training(request, training_id):
    training = get_object_or_404(Training, id=training_id, trainer=request.user)
    if request.method == 'POST':
        training.delete()
        return redirect('trainer_dashboard')
    return render(request, 'training/delete_training.html', {'training': training})

@login_required
def trainer_completions(request):
    trainer_trainings = Training.objects.filter(trainer=request.user)
    
    if not trainer_trainings.exists():
        registrations = TrainingRegistration.objects.none()
        messages.info(request, "You are not assigned as a trainer for any training sessions.")
        completed_count = 0
        not_completed_count = 0
    else:
        registrations = TrainingRegistration.objects.filter(
            training__in=trainer_trainings
        ).select_related('employee', 'training').order_by('-requested_at')
        
        status_filter = request.GET.get('status', '')
        complete_filter = request.GET.get('complete_status', '')
        
        if status_filter:
            registrations = registrations.filter(status=status_filter)
        
        if complete_filter:
            registrations = registrations.filter(complete_status=complete_filter)

        completed_count = registrations.filter(complete_status='Completed').count()
        not_completed_count = registrations.filter(complete_status='Not Completed').count()
        
    context = {
        'registrations': registrations,
        'status_filter': status_filter,
        'complete_filter': complete_filter,
        'STATUS_CHOICES': TrainingRegistration.STATUS_CHOICES,
        'COMPLETE_CHOICES': TrainingRegistration.COMPLETE_CHOICES,
        'completed_count': completed_count,
        'not_completed_count': not_completed_count,
        'total_count': registrations.count(),
    }
    
    return render(request, 'trainer/trainer_completions.html', context)

@login_required
def complete_registration(request, reg_id):
    registration = get_object_or_404(TrainingRegistration, id=reg_id)
    
    if registration.training.trainer != request.user:
        messages.error(request, "You are not authorized to update this registration.")
        return redirect('trainer_completions')
    
    if registration.complete_status == 'Completed':
        messages.info(request, "This registration is already marked as Completed.")
        return redirect('trainer_completions')
    
    registration.complete_status = 'Completed'
    registration.save()
    messages.success(request, f"Marked {registration.employee.username}'s registration as Completed.")
    
    return redirect('trainer_completions')

# ---------------- Employee ----------------
@login_required
def employee_dashboard(request):
    user = request.user
    user_profile = getattr(user, 'userprofile', None)
    user_department = user_profile.department if user_profile else None
    
    start_date_str = request.GET.get('start_date')
    end_date_str = request.GET.get('end_date')
    trainer_id = request.GET.get('trainer')

    trainings = Training.objects.all()
    if user_department:
        trainings = trainings.filter(department=user_department)

    if trainer_id:
        trainings = trainings.filter(trainer__id=trainer_id)

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

    registrations = TrainingRegistration.objects.filter(employee=user)

    trainers = User.objects.filter(groups__name='Trainer')

    context = {
        'trainings': trainings,
        'registrations': registrations,
        'start_date': start_date_str,
        'end_date': end_date_str,
        'user_department': user_department,
        'trainers': trainers,
        'selected_trainer': trainer_id,
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
