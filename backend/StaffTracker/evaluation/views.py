from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.apps import apps
from django.core.paginator import Paginator
from django.db.models import Avg

from .models import Evaluation
from .forms import EvaluationForm

def get_training_model():
    try:
        return apps.get_model('training', 'Training')
    except LookupError:
        return None

def get_registration_model():
    try:
        return apps.get_model('training', 'TrainingRegistration')
    except LookupError:
        return None

def can_user_evaluate_training(user, training):
    if Evaluation.objects.filter(user=user, training=training).exists():
        return False, "Already evaluated"
    
    Registration = get_registration_model()
    if Registration:
        try:
            registration = Registration.objects.get(
                training=training,
                employee=user
            )
            if registration.status != 'Approved':
                return False, f"Registration not approved (Status: {registration.status})"
            
            if registration.complete_status != 'Completed':
                return False, f"Training not completed (Status: {registration.complete_status})"
            
        except Registration.DoesNotExist:
            return False, "Not registered for this training"
    else:
        return False, "Registration model not available"
    
    return True, "Eligible for evaluation"

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
        can_evaluate, reason = can_user_evaluate_training(request.user, training)
        training.can_evaluate = can_evaluate
        training.evaluation_eligibility_reason = reason
        training.has_evaluated = Evaluation.objects.filter(
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
        return redirect('employee_dashboard')
    
    Registration = get_registration_model()
    if Registration:
        try:
            registration = Registration.objects.get(
                training=training,
                employee=request.user
            )
            if registration.status != 'Approved':
                messages.warning(request, 'Your registration is not approved.')
                return redirect('employee_dashboard')
            
            if registration.complete_status != 'Completed':
                messages.warning(request, 'This training is not completed yet.')
                return redirect('employee_dashboard')
            
        except Registration.DoesNotExist:
            messages.warning(request, 'You are not registered for this training.')
            return redirect('employee_dashboard')
    else:
        messages.error(request, 'Registration module is not available.')
        return redirect('employee_dashboard')
    
    if request.method == 'POST':
        form = EvaluationForm(request.POST)
        if form.is_valid():
            evaluation = form.save(commit=False)
            evaluation.user = request.user
            evaluation.training = training
            evaluation.save()
            messages.success(request, 'Evaluation submitted successfully!')
            return redirect('employee_dashboard')
    else:
        form = EvaluationForm()
    
    return render(request, 'evaluation/evaluate.html', {
        'form': form,
        'training': training
    })
    
@login_required
def trainer_evaluations(request, training_id=None):
    Training = get_training_model()
    if not Training:
        messages.error(request, 'Training module is not available.')
        return redirect('trainer_dashboard')
    
    trainer_trainings = Training.objects.filter(trainer=request.user)
    
    if training_id:
        try:
            training = trainer_trainings.get(id=training_id)
        except Training.DoesNotExist:
            messages.error(request, 'Training not found or you are not the trainer.')
            return redirect('trainer_evaluations')
        
        evaluations = Evaluation.objects.filter(training=training).select_related('user')
        
        avg_ratings = {
            'overall': evaluations.aggregate(Avg('rating'))['rating__avg'],
            'q1': evaluations.aggregate(Avg('question1_rating'))['question1_rating__avg'],
            'q2': evaluations.aggregate(Avg('question2_rating'))['question2_rating__avg'],
            'q3': evaluations.aggregate(Avg('question3_rating'))['question3_rating__avg'],
            'q4': evaluations.aggregate(Avg('question4_rating'))['question4_rating__avg'],
            'recommend_percentage': evaluations.filter(question5_would_recommend=True).count() / max(evaluations.count(), 1) * 100
        }
        
        question_scores = [avg_ratings['q1'], avg_ratings['q2'], avg_ratings['q3'], avg_ratings['q4']]
        avg_ratings['question_avg'] = round(sum(question_scores) / len(question_scores), 2)
        
        paginator = Paginator(evaluations, 10)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        
        return render(request, 'evaluation/trainer_evaluation_detail.html', {
            'training': training,
            'evaluations': page_obj,
            'avg_ratings': avg_ratings,
            'total_evaluations': evaluations.count(),
        })
    else:
        trainings_with_stats = []
        
        for training in trainer_trainings:
            evaluations = Evaluation.objects.filter(training=training)
            count = evaluations.count()
            
            if count > 0:
                avg_rating = evaluations.aggregate(Avg('rating'))['rating__avg']
                recommend_count = evaluations.filter(question5_would_recommend=True).count()
            else:
                avg_rating = None
                recommend_count = 0
            
            trainings_with_stats.append({
                'training': training,
                'evaluation_count': count,
                'avg_rating': round(avg_rating, 2) if avg_rating else 'N/A',
                'recommend_percentage': round((recommend_count / count * 100), 1) if count > 0 else 0,
            })
        
        return render(request, 'evaluation/trainer_evaluations.html', {
            'trainings_with_stats': trainings_with_stats,
        })    