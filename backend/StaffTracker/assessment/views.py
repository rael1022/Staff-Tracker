from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse

from training.models import Training
from .models import PreAssessment, PostAssessment, AssessmentQuestion


@login_required
def create_pre_assessment(request, training_id):
    training = get_object_or_404(Training, id=training_id)

    can_do = training.training_status == "Open"

    already_done = PreAssessment.objects.filter(
        training=training,
        user=request.user
    ).exists()

    if not can_do or already_done:
        return render(
            request,
            "frontend/assessment/pre_assessment_form.html",
            {
                "training": training,
                "disabled": True,
                "reason": "Pre-assessment not available"
            }
        )

    questions = AssessmentQuestion.objects.filter(
        training=training,
        question_type='pre'
    ).order_by('id')
    
    if not questions.exists():
        return render(
            request,
            "frontend/assessment/pre_assessment_form.html",
            {
                "training": training,
                "disabled": True,
                "reason": "No questions available for this assessment"
            }
        )

    if request.method == "POST":
        user_answers = {}
        correct_count = 0
        
        for question in questions:
            question_key = f"question_{question.id}"
            user_answer = request.POST.get(question_key)
            if user_answer:
                user_answers[str(question.id)] = user_answer
        
        pre_assessment = PreAssessment.objects.create(
            training=training,
            user=request.user,
            assessment_date=timezone.now(),
            stress_level=request.POST.get("stress_level"),
            status="Completed",
            user_answers=user_answers
        )
        
        pre_assessment.score = pre_assessment.calculate_score()
        pre_assessment.save()
        
        return redirect("pre_assessment")

    return render(
        request,
        "frontend/assessment/pre_assessment_form.html",
        {
            "training": training,
            "questions": questions,
            "disabled": False
        }
    )


@login_required
def create_post_assessment(request, training_id):
    training = get_object_or_404(Training, id=training_id)

    can_do = training.training_status == "Completed"

    already_done = PostAssessment.objects.filter(
        training=training,
        user=request.user
    ).exists()

    if not can_do or already_done:
        return render(
            request,
            "frontend/assessment/post_assessment_form.html",
            {
                "training": training,
                "disabled": True,
                "reason": "Post-assessment not available"
            }
        )

    questions = AssessmentQuestion.objects.filter(
        training=training,
        question_type='post'
    ).order_by('id')
    
    if not questions.exists():
        return render(
            request,
            "frontend/assessment/post_assessment_form.html",
            {
                "training": training,
                "disabled": True,
                "reason": "No questions available for this assessment"
            }
        )

    if request.method == "POST":
        user_answers = {}
        
        for question in questions:
            question_key = f"question_{question.id}"
            user_answer = request.POST.get(question_key)
            if user_answer:
                user_answers[str(question.id)] = user_answer
        
        post_assessment = PostAssessment.objects.create(
            training=training,
            user=request.user,
            assessment_date=timezone.now(),
            status="Completed",
            user_answers=user_answers
        )
        
        post_assessment.score = post_assessment.calculate_score()
        post_assessment.save()
        
        return redirect("post_assessment")

    return render(
        request,
        "frontend/assessment/post_assessment_form.html",
        {
            "training": training,
            "questions": questions,
            "disabled": False
        }
    )


@login_required
def get_assessment_questions(request, training_id, question_type):
    """API endpoint to get questions for a specific training and type"""
    if question_type not in ['pre', 'post']:
        return JsonResponse({'error': 'Invalid question type'}, status=400)
    
    questions = AssessmentQuestion.objects.filter(
        training_id=training_id,
        question_type=question_type
    ).order_by('id').values(
        'id', 'question_text', 'option_a', 'option_b', 
        'option_c', 'option_d', 'marks'
    )
    
    return JsonResponse({'questions': list(questions)})