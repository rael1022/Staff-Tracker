from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.contrib.auth.decorators import login_required

from training.models import Training
from .models import PreAssessment, PostAssessment


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

    if request.method == "POST":
        PreAssessment.objects.create(
            training=training,
            user=request.user,
            assessment_date=timezone.now(),
            score=request.POST.get("score"),
            stress_level=request.POST.get("stress_level"),
            status="Completed"
        )
        return redirect("pre_assessment")

    return render(
        request,
        "frontend/assessment/pre_assessment_form.html",
        {
            "training": training,
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

    if request.method == "POST":
        PostAssessment.objects.create(
            training=training,
            user=request.user,
            assessment_date=timezone.now(),
            score=request.POST.get("score"),
            status="Completed"
        )
        return redirect("post_assessment")

    return render(
        request,
        "frontend/assessment/post_assessment_form.html",
        {
            "training": training,
            "disabled": False
        }
    )
