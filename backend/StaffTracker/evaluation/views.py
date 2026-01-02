# evaluation/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.apps import apps

from .models import Evaluation
from .forms import EvaluationForm

def get_training_model():
    try:
        return apps.get_model('training', 'Training')
    except LookupError:
        return None

@login_required
def evaluation_dashboard(request):
    Training = get_training_model()
    if not Training:
        return render(request, 'evaluation/evaluation_dashboard.html', {
            'trainings': [],
            'error_message': 'Training module is not available.'
        })
    
    trainings = Training.objects.all()
    
    for training in trainings:
        training.can_evaluate = not Evaluation.objects.filter(
            user=request.user, 
            training=training
        ).exists()
    
    return render(request, 'evaluation/evaluation_dashboard.html', {
        'trainings': trainings,
        'error_message': None
    })

@login_required
def submit_evaluation(request, training_id):
    Training = get_training_model()
    if not Training:
        messages.error(request, 'Training module is not available.')
        return redirect('evaluation_dashboard')
    
    try:
        training = Training.objects.get(pk=training_id)
    except Training.DoesNotExist:
        messages.error(request, 'Training not found.')
        return redirect('evaluation_dashboard')
    
    if Evaluation.objects.filter(user=request.user, training=training).exists():
        messages.warning(request, 'You have already evaluated this training.')
        return redirect('evaluation_dashboard')
    
    if request.method == 'POST':
        form = EvaluationForm(request.POST)
        if form.is_valid():
            evaluation = form.save(commit=False)
            evaluation.user = request.user
            evaluation.training = training
            evaluation.save()
            
            messages.success(request, 'Evaluation submitted successfully!')
            return redirect('evaluation_dashboard')
    else:
        form = EvaluationForm()
    
    return render(request, 'evaluation/evaluate.html', {
        'form': form,
        'training': training
    })