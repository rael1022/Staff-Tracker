from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Evaluation
from training.models import Training

User = get_user_model()

class UserInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'role', 'account_status']

class TrainingInfoSerializer(serializers.ModelSerializer):
    trainer_name = serializers.CharField(source='trainer.get_full_name', read_only=True)
    
    class Meta:
        model = Training
        fields = ['training_id', 'training_title', 'training_description', 
                 'training_mode', 'training_status', 'location', 'trainer_name']

class EvaluationSerializer(serializers.ModelSerializer):
    user_info = UserInfoSerializer(source='user', read_only=True)
    username = serializers.CharField(source='user.username', read_only=True)
    user_role = serializers.CharField(source='user.role', read_only=True)
    
    training_info = TrainingInfoSerializer(source='training', read_only=True)
    training_title = serializers.CharField(source='training.training_title', read_only=True)
    
    average_question_rating = serializers.SerializerMethodField()
    is_editable = serializers.SerializerMethodField()
    
    class Meta:
        model = Evaluation
        fields = [
            'evaluation_id',
            'training',
            'training_info',
            'training_title',
            'user',
            'user_info',
            'username',
            'user_role',
            
            'rating',
            'feedback',
            'question1_rating',
            'question2_rating',
            'question3_rating',
            'question4_rating',
            'question5_would_recommend',
            
            'evaluation_date',
            
            'average_question_rating',
            'is_editable'
        ]
        read_only_fields = [
            'evaluation_id', 'evaluation_date', 'user', 
            'user_info', 'username', 'user_role',
            'training_info', 'training_title',
            'average_question_rating', 'is_editable'
        ]
    
    def get_average_question_rating(self, obj):
        return obj.get_average_question_rating()
    
    def get_is_editable(self, obj):
        request = self.context.get('request')
        if not request:
            return False
        
        if obj.user != request.user:
            return False
        
        time_since_submission = timezone.now() - obj.evaluation_date
        return time_since_submission.total_seconds() <= 24 * 3600
    
    def validate(self, data):
        request = self.context.get('request')
        user = request.user if request else None
        
        if not user or user.account_status != 'Active':
            raise serializers.ValidationError("Your account is not active.")
        
        training = data.get('training')
        
        if self.instance:  
            if self.instance.user != user and user.role != 'Admin':
                raise serializers.ValidationError("You can only edit your own evaluations.")
            
            time_since_submission = timezone.now() - self.instance.evaluation_date
            if time_since_submission.total_seconds() > 24 * 3600 and user.role != 'Admin':
                raise serializers.ValidationError("Evaluation can only be edited within 24 hours.")
            
            training = training or self.instance.training
        else:  
            if Evaluation.objects.filter(user=user, training=training).exists():
                raise serializers.ValidationError({
                    'training': 'You have already submitted an evaluation for this training.'
                })
        
        if training.training_status != 'Completed':
            raise serializers.ValidationError({
                'training': 'You can only submit evaluations for completed trainings.'
            })
        
        return data

class EvaluationCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Evaluation
        fields = [
            'training',
            'rating',
            'feedback',
            'question1_rating',
            'question2_rating',
            'question3_rating',
            'question4_rating',
            'question5_would_recommend'
        ]

class EvaluationStatsSerializer(serializers.Serializer):
    total_evaluations = serializers.IntegerField()
    average_overall_rating = serializers.FloatField()
    recommendation_rate = serializers.FloatField()
    rating_distribution = serializers.DictField()
    by_department = serializers.DictField()
    by_training_mode = serializers.DictField()