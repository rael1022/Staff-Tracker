from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
import csv
import json
from datetime import datetime, timedelta

from training.models import Training, TrainingRegistration
from .models import PreAssessment, PostAssessment, AssessmentQuestion

@login_required
def create_pre_assessment(request, training_id):
    training = get_object_or_404(Training, id=training_id)
    
    registration = TrainingRegistration.objects.filter(
        training=training,
        employee=request.user,
        status='Approved'
    ).exists()
    
    if not registration:
        messages.error(request, "You need to be registered for this training to take the pre-assessment.")
        return redirect('employee_dashboard')
    
    already_done = PreAssessment.objects.filter(
        training=training,
        user=request.user
    ).exists()
    
    if already_done:
        messages.info(request, "You have already completed the pre-assessment for this training.")
        return redirect('employee_dashboard')
    
    # 检查时间条件：培训开始前2小时开放（暂时屏蔽）
    # training_datetime = datetime.combine(training.date, training.time)
    # if timezone.now() < training_datetime - timedelta(hours=2):
    #     messages.info(request, "Pre-assessment will open 2 hours before the training starts.")
    #     return redirect('employee_dashboard')
    
    questions = AssessmentQuestion.objects.filter(
        training=training,
        question_type='pre'
    ).order_by('id')
    
    if not questions.exists():
        messages.error(request, "No pre-assessment questions available for this training.")
        return redirect('employee_dashboard')
    
    if request.method == "POST":
        correct_count = 0
        total_questions = questions.count()
        
        for question in questions:
            question_key = f"question_{question.id}"
            user_answer = request.POST.get(question_key)
            if user_answer and user_answer.upper() == question.correct_answer:
                correct_count += 1
        
        score = (correct_count / total_questions) * 100 if total_questions > 0 else 0
        
        PreAssessment.objects.create(
            training=training,
            user=request.user,
            score=round(score, 2),
            stress_level=request.POST.get("stress_level", ""),
            status="Completed"
        )
        
        messages.success(request, f"Pre-assessment completed! Your score: {round(score, 2)}%")
        return redirect('employee_results')
    
    return render(
        request,
        "assessment/pre_assessment_form.html",
        {
            "training": training,
            "questions": questions,
        }
    )

@login_required
def create_post_assessment(request, training_id):
    training = get_object_or_404(Training, id=training_id)
    
    registration = TrainingRegistration.objects.filter(
        training=training,
        employee=request.user,
        status='Approved'
    ).exists()
    
    if not registration:
        messages.error(request, "You need to be registered for this training to take the post-assessment.")
        return redirect('employee_dashboard')
    
    already_done = PostAssessment.objects.filter(
        training=training,
        user=request.user
    ).exists()
    
    if already_done:
        messages.info(request, "You have already completed the post-assessment for this training.")
        return redirect('employee_dashboard')
    
    pre_done = PreAssessment.objects.filter(
        training=training,
        user=request.user,
        status='Completed'
    ).exists()
    
    if not pre_done:
        messages.warning(request, "You need to complete the pre-assessment first.")
        return redirect('employee_dashboard')
    
    training_datetime = datetime.combine(training.date, training.time)
    training_end_datetime = training_datetime + timedelta(hours=2)
    
    if timezone.now() < training_end_datetime:
        messages.info(request, "Post-assessment is only available after training completion.")
        return redirect('employee_dashboard')
    
    questions = AssessmentQuestion.objects.filter(
        training=training,
        question_type='post'
    ).order_by('id')
    
    if not questions.exists():
        messages.error(request, "No post-assessment questions available for this training.")
        return redirect('employee_dashboard')
    
    if request.method == "POST":
        correct_count = 0
        total_questions = questions.count()
        
        for question in questions:
            question_key = f"question_{question.id}"
            user_answer = request.POST.get(question_key)
            if user_answer and user_answer.upper() == question.correct_answer:
                correct_count += 1
        
        score = (correct_count / total_questions) * 100 if total_questions > 0 else 0
        
        PostAssessment.objects.create(
            training=training,
            user=request.user,
            score=round(score, 2),
            status="Completed"
        )
        
        messages.success(request, f"Post-assessment completed! Your score: {round(score, 2)}%")
        return redirect('employee_results')
    
    return render(
        request,
        "assessment/post_assessment_form.html",
        {
            "training": training,
            "questions": questions,
        }
    )

@login_required
def manage_assessment_questions(request, training_id=None):
    if not request.user.groups.filter(name='Trainer').exists():
        return redirect('trainer_dashboard')

    trainings = Training.objects.filter(trainer=request.user)
    selected_training = None
    questions = None

    if training_id is None and trainings.exists():
        return redirect(
            'manage_assessment_questions_training',
            training_id=trainings.first().id
        )

    if training_id:
        selected_training = get_object_or_404(
            Training,
            id=training_id,
            trainer=request.user
        )
        questions = AssessmentQuestion.objects.filter(
            training=selected_training
        ).order_by('question_type', 'id')
        
    if request.method == 'POST':

        if 'add_question' in request.POST:
            question_type = request.POST.get('question_type')
            question_text = request.POST.get('question_text')
            option_a = request.POST.get('option_a')
            option_b = request.POST.get('option_b')
            option_c = request.POST.get('option_c')
            option_d = request.POST.get('option_d')
            correct_answer = request.POST.get('correct_answer')
            marks = request.POST.get('marks', 1)

            if selected_training and question_text:
                exists = AssessmentQuestion.objects.filter(
                    training=selected_training,
                    question_type=question_type,
                    question_text=question_text
                ).exists()

                if not exists:
                    AssessmentQuestion.objects.create(
                        training=selected_training,
                        question_type=question_type,
                        question_text=question_text,
                        option_a=option_a,
                        option_b=option_b,
                        option_c=option_c,
                        option_d=option_d,
                        correct_answer=correct_answer,
                        marks=marks
                    )
                    messages.success(request, 'Question added successfully!')
                else:
                    messages.error(request, 'This question already exists.')

            return redirect(
                'manage_assessment_questions_training',
                training_id=training_id
            )

        elif 'import_questions' in request.POST:
            if 'question_file' in request.FILES:
                file = request.FILES['question_file']
                ext = file.name.split('.')[-1].lower()

                try:
                    if ext == 'csv':
                        decoded = file.read().decode('utf-8').splitlines()
                        reader = csv.DictReader(decoded)

                        for row in reader:
                            AssessmentQuestion.objects.get_or_create(
                                training=selected_training,
                                question_type=row['type'].strip().lower(),
                                question_text=row['question'].strip(),
                                defaults={
                                    'option_a': row['option_a'],
                                    'option_b': row['option_b'],
                                    'option_c': row['option_c'],
                                    'option_d': row['option_d'],
                                    'correct_answer': row['correct_answer'].strip().upper(),
                                    'marks': int(row.get('marks', 1))
                                }
                            )

                    elif ext == 'json':
                        data = json.loads(file.read().decode('utf-8'))
                        for item in data:
                            AssessmentQuestion.objects.get_or_create(
                                training=selected_training,
                                question_type=item['type'].strip().lower(),
                                question_text=item['question'].strip(),
                                defaults={
                                    'option_a': item['option_a'],
                                    'option_b': item['option_b'],
                                    'option_c': item['option_c'],
                                    'option_d': item['option_d'],
                                    'correct_answer': item['correct_answer'].strip().upper(),
                                    'marks': int(item.get('marks', 1))
                                }
                            )

                    messages.success(request, 'Questions imported successfully.')

                except Exception as e:
                    messages.error(request, f'Import error: {e}')

            return redirect(
                'manage_assessment_questions_training',
                training_id=training_id
            )

        elif 'delete_question' in request.POST:
            question_id = request.POST.get('question_id')
            question = get_object_or_404(
                AssessmentQuestion,
                id=question_id,
                training__trainer=request.user
            )
            question.delete()
            messages.success(request, 'Question deleted.')

            return redirect(
                'manage_assessment_questions_training',
                training_id=training_id
            )

    return render(
        request,
        'trainer/manage_questions.html',
        {
            'trainings': trainings,
            'selected_training': selected_training,
            'questions': questions,
            'question_types': AssessmentQuestion.TYPE_CHOICES,
        }
    )

@login_required
def view_results(request, training_id=None):
    if not request.user.groups.filter(name='Trainer').exists():
        return redirect('trainer_dashboard')
    
    trainings = Training.objects.filter(trainer=request.user)
    selected_training = None
    pre_results = []
    post_results = []
    
    if training_id:
        selected_training = get_object_or_404(Training, id=training_id, trainer=request.user)
        
        pre_results = PreAssessment.objects.filter(
            training=selected_training,
            status='Completed'
        ).select_related('user').order_by('-score')
        
        post_results = PostAssessment.objects.filter(
            training=selected_training,
            status='Completed'
        ).select_related('user').order_by('-score')
    elif request.method == 'GET' and trainings.exists():
        return redirect('view_results_training', training_id=trainings.first().id)
    
    context = {
        'trainings': trainings,
        'selected_training': selected_training,
        'pre_results': pre_results,
        'post_results': post_results,
    }
    return render(request, 'trainer/view_results.html', context)

@login_required
def employee_results(request):
    registrations = TrainingRegistration.objects.filter(
        employee=request.user,
        status='Approved'
    ).select_related('training')
    
    pre_assessments = PreAssessment.objects.filter(
        user=request.user,
        status='Completed'
    ).select_related('training').order_by('-assessment_date')
    
    post_assessments = PostAssessment.objects.filter(
        user=request.user,
        status='Completed'
    ).select_related('training').order_by('-assessment_date')
    
    all_scores = []
    
    for pre in pre_assessments:
        all_scores.append(float(pre.score))

    for post in post_assessments:
        all_scores.append(float(post.score))
    
    average_score = round(sum(all_scores) / len(all_scores), 1) if all_scores else None
    
    registration_status = []

    for reg in registrations:
        training = reg.training

        pre_done = PreAssessment.objects.filter(
            training=training,
            user=request.user,
            status='Completed'
        ).exists()

        post_done = PostAssessment.objects.filter(
            training=training,
            user=request.user,
            status='Completed'
        ).exists()

        registration_status.append({
            'registration': reg,
            'pre_done': pre_done,
            'post_done': post_done,
        })
    
    context = {
        'pre_assessments': pre_assessments,
        'post_assessments': post_assessments,
        'registrations': registration_status,
        'average_score': average_score,
    }
    return render(request, 'assessment/employee_results.html', context)