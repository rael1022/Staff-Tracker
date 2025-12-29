from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    EvaluationViewSet,
    DepartmentEvaluationsView,
    TrainerEvaluationsView,
    submit_evaluation
)

router = DefaultRouter()
router.register(r'evaluations', EvaluationViewSet, basename='evaluation')

urlpatterns = [
    path('', include(router.urls)),
    
    path(
        'trainings/<int:training_id>/submit-evaluation/',
        submit_evaluation,
        name='submit-evaluation'
    ),
    
    path(
        'department/evaluations/',
        DepartmentEvaluationsView.as_view(),
        name='department-evaluations'
    ),
    path(
        'trainer/evaluations/',
        TrainerEvaluationsView.as_view(),
        name='trainer-evaluations'
    ),
    
    path(
        'evaluations/stats/summary/',
        EvaluationViewSet.as_view({'get': 'stats'}),
        name='evaluation-stats'
    ),
]