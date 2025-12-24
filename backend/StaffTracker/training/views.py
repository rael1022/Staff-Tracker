from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Training, TrainingRegistration

# ---------------- Trainer ----------------
@login_required
def trainer_dashboard(request):
    trainings = Training.objects.filter(trainer=request.user)
    return render(request, 'training/training_dashboard.html', {'trainings': trainings})

@login_required
def create_training(request):
    if request.method == 'POST':
        Training.objects.create(
            title=request.POST['title'],
            description=request.POST['description'],
            date=request.POST['date'],
            time=request.POST['time'],
            location=request.POST['location'],
            trainer=request.user
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
