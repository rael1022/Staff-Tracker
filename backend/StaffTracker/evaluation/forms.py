from django import forms
from .models import Evaluation

class EvaluationForm(forms.ModelForm):
    class Meta:
        model = Evaluation
        fields = [
            'rating',
            'question1_rating',
            'question2_rating',
            'question3_rating',
            'question4_rating',
            'question5_would_recommend',
            'feedback'
        ]
