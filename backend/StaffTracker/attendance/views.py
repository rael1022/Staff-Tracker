from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.utils import timezone
from .models import Attendance
from .serializers import (
    QRAttendanceSerializer, 
    UserLoginSerializer, 
    GenerateQRSerializer,
    AttendanceSerializer
)
import json
import qrcode
import base64
import io
import time

@api_view(['POST'])
def generate_qr_code(request):
    serializer = GenerateQRSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    training_id = serializer.validated_data['training_id']
    training_title = serializer.validated_data.get('training_title', 'Training Session')
    
    qr_data = {
        "type": "attendance_checkin",
        "training_id": training_id,
        "training_title": training_title,
        "timestamp": int(time.time()),
        "expires": int(time.time()) + 3600,
        "generated_at": timezone.now().isoformat()
    }
    
    qr_json = json.dumps(qr_data)
    
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(qr_json)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)
    img_base64 = base64.b64encode(buffer.read()).decode()
    
    return Response({
        'success': True,
        'message': 'QR code generated successfully',
        'training_id': training_id,
        'training_title': training_title,
        'qr_data': qr_json,
        'qr_image': f"data:image/png;base64,{img_base64}",
        'expires_at': qr_data['expires'],
        'expires_human': timezone.datetime.fromtimestamp(qr_data['expires']).strftime('%Y-%m-%d %H:%M:%S')
    })

@api_view(['POST'])
def scan_qr_code(request):
    serializer = QRAttendanceSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    qr_data = serializer.validated_data['qr_data']
    training_id = serializer.validated_data['training_id']
    
    try:
        qr_json = json.loads(qr_data)
        
        if qr_json.get('type') != 'attendance_checkin':
            return Response({
                'success': False,
                'message': 'This is not a check-in QR code'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if qr_json.get('training_id') != training_id:
            return Response({
                'success': False,
                'message': 'The QR code does not match the training.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        current_time = int(time.time())
        if qr_json.get('expires', 0) < current_time:
            return Response({
                'success': False,
                'message': 'The QR code has expired. Please generate a new one.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        attendance = Attendance.objects.create(
            training_id=training_id,
            qr_code_data=qr_data,
            qr_scan_time=timezone.now(),
            status=Attendance.Status.ABSENT,
            date=timezone.now().date(),
        )
        
        return Response({
            'success': True,
            'message': 'Please log in to verify your identity.',
            'attendance_id': str(attendance.id),
            'requires_login': True,
            'training_title': qr_json.get('training_title', 'Unknown Training'),
            'training_id': training_id
        })
        
    except json.JSONDecodeError:
        return Response({
            'success': False,
            'message': 'QR code format error'
        }, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
def verify_user_and_checkin(request):
    serializer = UserLoginSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    username = serializer.validated_data['username']
    password = serializer.validated_data['password']
    attendance_id = serializer.validated_data['attendance_id']
    qr_data = serializer.validated_data['qr_data']
    
    try:
        attendance = Attendance.objects.get(id=attendance_id)
        
        if attendance.qr_code_data != qr_data:
            return Response({
                'success': False,
                'message': 'QR code mismatch'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if attendance.is_qr_used:
            return Response({
                'success': False,
                'message': 'This QR code has already been used.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        user = verify_user_credentials(username, password)
        
        if not user:
            return Response({
                'success': False,
                'message': 'Username or password incorrect.'
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        existing = Attendance.objects.filter(
            user_id=username,
            training_id=attendance.training_id,
            status=Attendance.Status.PRESENT
        ).exclude(id=attendance_id).first()
        
        if existing:
            return Response({
                'success': False,
                'message': 'You have already checked in for this training.',
                'previous_checkin': existing.check_in_time
            }, status=status.HTTP_400_BAD_REQUEST)
        
        attendance.user_id = username
        attendance.status = Attendance.Status.PRESENT
        attendance.check_in_time = timezone.now()
        attendance.is_qr_used = True
        attendance.save()
        
        return Response({
            'success': True,
            'message': 'Check-in successful!',
            'attendance': {
                'id': str(attendance.id),
                'username': attendance.user_id,
                'training_id': attendance.training_id,
                'status': attendance.status,
                'check_in_time': attendance.check_in_time,
                'date': attendance.date
            }
        })
        
    except Attendance.DoesNotExist:
        return Response({
            'success': False,
            'message': 'Sign-in record does not exist'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_400_BAD_REQUEST)

def verify_user_credentials(username, password):
    try:
        from django.contrib.auth import authenticate
        
        user = authenticate(username=username, password=password)
        if user:
            print(f"User verification successful.: {username}")
            return user
        else:
            print(f"User verification failed.: {username}")
            return None
    except Exception as e:
        print(f"Validation error: {e}")
        return None

@api_view(['GET'])
def get_attendance_by_training(request, training_id):
    attendances = Attendance.objects.filter(training_id=training_id)
    
    data = []
    for att in attendances:
        data.append({
            'id': str(att.id),
            'username': att.user_id,
            'status': att.status,
            'check_in_time': att.check_in_time,
            'date': att.date,
            'is_qr_used': att.is_qr_used
        })
    
    present_count = attendances.filter(status=Attendance.Status.PRESENT).count()
    
    return Response({
        'training_id': training_id,
        'total': attendances.count(),
        'present': present_count,
        'absent': attendances.count() - present_count,
        'attendances': data
    })

@api_view(['GET'])
def get_all_attendances(request):
    attendances = Attendance.objects.all().order_by('-date', '-check_in_time')
    serializer = AttendanceSerializer(attendances, many=True)
    return Response(serializer.data)