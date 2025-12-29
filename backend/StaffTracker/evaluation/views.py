from rest_framework import viewsets, status, generics, filters, mixins
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Avg, Count, Q, F
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta, datetime
from .models import Evaluation
from training.models import Training
from .serializers import (
    EvaluationSerializer, 
    EvaluationCreateSerializer,
    EvaluationStatsSerializer
)
from .permissions import (
    IsOwnerOrAdmin, 
    CanSubmitEvaluation,
    IsAdminOrTrainer,
    IsAdminHODOrTrainer
)

User = get_user_model()

class EvaluationViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, CanSubmitEvaluation]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = [
        'training__training_title', 
        'feedback',
        'user__username',
        'user__email'
    ]
    ordering_fields = [
        'evaluation_date', 
        'rating',
        'training__training_title'
    ]
    
    def get_serializer_class(self):
        if self.action == 'create':
            return EvaluationCreateSerializer
        return EvaluationSerializer
    
    def get_permissions(self):
        if self.action in ['update', 'partial_update', 'destroy']:
            return [IsAuthenticated(), IsOwnerOrAdmin()]
        return super().get_permissions()
    
    def get_queryset(self):
        user = self.request.user
        
        queryset = Evaluation.objects.select_related(
            'training', 'user'
        ).prefetch_related('training__trainer')
        
        if user.role == 'Admin':
            pass
        elif user.role == 'HOD':
            queryset = queryset.filter(user__department=user.department)
        elif user.role == 'Trainer':
            queryset = queryset.filter(training__trainer=user)
        else:
            queryset = queryset.filter(user=user)
        
        return queryset
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
    
    def perform_update(self, serializer):
        serializer.save()
    
    @action(detail=False, methods=['get'])
    def my_evaluations(self, request):
        queryset = self.get_queryset().filter(user=request.user)
        page = self.paginate_queryset(queryset)
        
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def pending(self, request):
        user = request.user
        
        completed_trainings = Training.objects.filter(
            training_status='Completed',
            participants=user
        ).exclude(
            evaluations__user=user
        ).select_related('trainer')
        
        pending_trainings = []
        for training in completed_trainings:
            pending_trainings.append({
                'training_id': training.training_id,
                'training_title': training.training_title,
                'training_description': training.training_description[:150] + '...' if training.training_description else '',
                'trainer_name': training.trainer.get_full_name() if training.trainer else 'N/A',
                'training_mode': training.training_mode,
                'location': training.location,
                'completed_date': getattr(training, 'end_date', None),
            })
        
        return Response(pending_trainings)
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        if request.user.role != 'Admin':
            return Response(
                {'error': 'Permission denied'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        total_evaluations = Evaluation.objects.count()
        average_overall_rating = Evaluation.objects.aggregate(
            avg=Avg('rating')
        )['avg'] or 0
        recommendation_rate = Evaluation.objects.filter(
            question5_would_recommend=True
        ).count() / total_evaluations * 100 if total_evaluations > 0 else 0
        
        rating_distribution = {}
        for i in range(1, 6):
            count = Evaluation.objects.filter(rating=i).count()
            rating_distribution[str(i)] = count
        
        by_department = {}
        if hasattr(User, 'department'):
            department_stats = Evaluation.objects.values(
                'user__department'
            ).annotate(
                count=Count('evaluation_id'),
                avg_rating=Avg('rating')
            )
            for stat in department_stats:
                dept = stat['user__department'] or 'Unknown'
                by_department[dept] = {
                    'count': stat['count'],
                    'avg_rating': round(stat['avg_rating'] or 0, 2)
                }
        
        by_training_mode = {}
        mode_stats = Evaluation.objects.values(
            'training__training_mode'
        ).annotate(
            count=Count('evaluation_id'),
            avg_rating=Avg('rating')
        )
        for stat in mode_stats:
            mode = stat['training__training_mode'] or 'Unknown'
            by_training_mode[mode] = {
                'count': stat['count'],
                'avg_rating': round(stat['avg_rating'] or 0, 2)
            }
        
        stats = {
            'total_evaluations': total_evaluations,
            'average_overall_rating': round(average_overall_rating, 2),
            'recommendation_rate': round(recommendation_rate, 2),
            'rating_distribution': rating_distribution,
            'by_department': by_department,
            'by_training_mode': by_training_mode,
            'last_updated': timezone.now()
        }
        
        serializer = EvaluationStatsSerializer(stats)
        return Response(serializer.data)

class DepartmentEvaluationsView(generics.ListAPIView):
    serializer_class = EvaluationSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        
        if user.role != 'HOD':
            return Evaluation.objects.none()
        
        return Evaluation.objects.filter(
            user__department=user.department
        ).select_related('training', 'user')

class TrainerEvaluationsView(generics.ListAPIView):
    serializer_class = EvaluationSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        
        if user.role != 'Trainer':
            return Evaluation.objects.none()
        
        return Evaluation.objects.filter(
            training__trainer=user
        ).select_related('training', 'user')

@api_view(['POST'])
@permission_classes([IsAuthenticated, CanSubmitEvaluation])
def submit_evaluation(request, training_id):
    try:
        training = Training.objects.get(pk=training_id)
    except Training.DoesNotExist:
        return Response(
            {'error': 'Training not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    if Evaluation.objects.filter(user=request.user, training=training).exists():
        return Response(
            {'error': 'You have already submitted an evaluation for this training.'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    if training.training_status != 'Completed':
        return Response(
            {'error': 'You can only submit evaluations for completed trainings.'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    serializer = EvaluationCreateSerializer(data=request.data)
    if serializer.is_valid():
        evaluation = serializer.save(
            user=request.user,
            training=training
        )
        
        full_serializer = EvaluationSerializer(evaluation, context={'request': request})
        return Response(full_serializer.data, status=status.HTTP_201_CREATED)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)