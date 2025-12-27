from rest_framework import serializers
from .models import Attendance

class QRAttendanceSerializer(serializers.Serializer):
    qr_data = serializers.CharField(required=True)
    training_id = serializers.CharField(required=True)

class UserLoginSerializer(serializers.Serializer):
    username = serializers.CharField(required=True)
    password = serializers.CharField(required=True, write_only=True)
    attendance_id = serializers.UUIDField(required=True)
    qr_data = serializers.CharField(required=True)

class GenerateQRSerializer(serializers.Serializer):
    training_id = serializers.CharField(required=True)
    training_title = serializers.CharField(required=False, default="Training Session")

class AttendanceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Attendance
        fields = '__all__'