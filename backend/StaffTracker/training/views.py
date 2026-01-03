from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from .models import Training, TrainingRegistration

# ---------------- HR ----------------
def is_hr(user):
    return user.groups.filter(name='HR').exists() or user.is_superuser

@login_required
@user_passes_test(is_hr)
def hr_dashboard(request):
    trainings = Training.objects.all()  
    return render(request, 'training/hr_training_dashboard.html', {'trainings': trainings})

@login_required
@user_passes_test(is_hr)
def hr_create_training(request):
    if request.method == 'POST':
        cpd_points = request.POST.get('cpd_points', 0) 
        trainer_id = request.POST.get('trainer_id')  
        trainer_user = None
        if trainer_id:
            from django.contrib.auth.models import User
            try:
                trainer_user = User.objects.get(id=trainer_id)
            except User.DoesNotExist:
                trainer_user = None

        Training.objects.create(
            title=request.POST['title'],
            description=request.POST['description'],
            date=request.POST['date'],
            time=request.POST['time'],
            location=request.POST['location'],
            trainer=trainer_user,
            cpd_points=cpd_points
        )
        messages.success(request, "Training created successfully")
        return redirect('hr_dashboard')

    from django.contrib.auth.models import User
    trainers = User.objects.filter(groups__name='Trainer')
    return render(request, 'training/hr_create_training.html', {'trainers': trainers})

@login_required
@user_passes_test(is_hr)
def hr_edit_training(request, training_id):
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
                training.cpd_points = int(cpd_points)
            except ValueError:
                training.cpd_points = 0

        trainer_id = request.POST.get('trainer_id')
        if trainer_id:
            from django.contrib.auth.models import User
            try:
                training.trainer = User.objects.get(id=trainer_id)
            except User.DoesNotExist:
                training.trainer = None

        from datetime import datetime
        if date_str:
            training.date = datetime.strptime(date_str, '%Y-%m-%d').date()
        if time_str:
            training.time = datetime.strptime(time_str, '%H:%M').time()

        training.save()
        messages.success(request, "Training updated successfully")
        return redirect('hr_dashboard')

    from django.contrib.auth.models import User
    trainers = User.objects.filter(groups__name='Trainer')
    return render(request, 'training/hr_edit_training.html', {'training': training, 'trainers': trainers})

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
    trainings = Training.objects.filter(trainer=request.user)
    return render(request, 'training/training_dashboard.html', {'trainings': trainings})

@login_required
def create_training(request):
    if request.method == 'POST':
        cpd_points = request.POST.get('cpd_points', 0) 
        Training.objects.create(
            title=request.POST['title'],
            description=request.POST['description'],
            date=request.POST['date'],
            time=request.POST['time'],
            location=request.POST['location'],
            trainer=request.user,
            cpd_points=cpd_points
        )
        return redirect('trainer_dashboard')
    return render(request, 'training/create_training.html')


@login_required
def edit_training(request, training_id):
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
                training.cpd_points = int(cpd_points)
            except ValueError:
                training.cpd_points = 0

        from datetime import datetime
        if date_str:
            training.date = datetime.strptime(date_str, '%Y-%m-%d').date()
        if time_str:
            training.time = datetime.strptime(time_str, '%H:%M').time()

        training.save()
        messages.success(request, "Training updated successfully")
        return redirect('trainer_dashboard')

    return render(request, 'training/edit_training.html', {'training': training})


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
    trainings = Training.objects.all()
    registrations = TrainingRegistration.objects.filter(employee=request.user)
    return render(request, 'training/employee_list.html', {
        'trainings': trainings,
        'registrations': registrations
    })

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
