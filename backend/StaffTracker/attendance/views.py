from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.contrib.auth import authenticate
from django.utils import timezone
from .models import Attendance
from .serializers import (
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
    
    attendance = Attendance.objects.create(
        training_id=training_id,
        status=Attendance.Status.ABSENT,
        date=timezone.now().date(),
    )
    
    qr_data = {
        "type": "attendance_checkin",
        "training_id": training_id,
        "training_title": training_title,
        "attendance_id": str(attendance.id), 
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
        'attendance_id': str(attendance.id),
        'training_id': training_id,
        'training_title': training_title,
        'qr_data': qr_json,
        'qr_image': f"data:image/png;base64,{img_base64}",
        'expires_at': qr_data['expires'],
        'expires_human': timezone.datetime.fromtimestamp(qr_data['expires']).strftime('%Y-%m-%d %H:%M:%S')
    })

@api_view(['POST'])
def scan_qr_code(request):
    try:
        qr_data = request.data.get('qr_data')
        if not qr_data:
            return Response({
                'success': False,
                'message': 'QR code data is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        qr_json = json.loads(qr_data)
        
        if qr_json.get('type') != 'attendance_checkin':
            return Response({
                'success': False,
                'message': 'This is not a check-in QR code'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        current_time = int(time.time())
        if qr_json.get('expires', 0) < current_time:
            return Response({
                'success': False,
                'message': 'The QR code has expired. Please generate a new one.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        attendance_id = qr_json.get('attendance_id')
        try:
            attendance = Attendance.objects.get(id=attendance_id)
        except Attendance.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Attendance record not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        if attendance.user_id:
            return Response({
                'success': False,
                'message': 'This QR code has already been used for check-in'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        return Response({
            'success': True,
            'message': 'Please enter your credentials to check in.',
            'attendance_id': attendance_id,
            'training_title': qr_json.get('training_title', 'Unknown Training'),
            'training_id': qr_json.get('training_id')
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
    
    try:
        attendance = Attendance.objects.get(id=attendance_id)
        
        if attendance.user:
            return Response({
                'success': False,
                'message': 'This attendance record has already been used.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        user = authenticate(username=username, password=password)
        if not user:
            return Response({
                'success': False,
                'message': 'Username or password incorrect.'
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        try:
            if not hasattr(user, 'role') or user.role != 'employee':
                return Response({
                    'success': False,
                    'message': 'Only employees can check in for training.'
                }, status=status.HTTP_403_FORBIDDEN)
        except AttributeError:
            return Response({
                'success': False,
                'message': 'User role information not found.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            from register.models import Register
            
            register_record = Register.objects.filter(
                user_id=user.id,
                training_id=attendance.training_id
            ).first()
            
            if not register_record:
                return Response({
                    'success': False,
                    'message': 'You are not registered for this training.'
                }, status=status.HTTP_403_FORBIDDEN)
            
            if register_record.approval_status != 'Approved':
                return Response({
                    'success': False,
                    'message': 'Your registration for this training is not approved.'
                }, status=status.HTTP_403_FORBIDDEN)
                
        except ImportError:
            print("Warning: Register model not found, skipping approval check")
        except Exception as e:
            print(f"Error checking register approval: {e}")
            return Response({
                'success': False,
                'message': 'Error checking training registration approval.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        existing = Attendance.objects.filter(
            user=user,
            training_id=attendance.training_id,
            status=Attendance.Status.PRESENT
        ).exclude(id=attendance_id).first()
        
        if existing:
            return Response({
                'success': False,
                'message': 'You have already checked in for this training.',
                'previous_checkin': existing.check_in_time
            }, status=status.HTTP_400_BAD_REQUEST)
        
        attendance.user = user
        attendance.status = Attendance.Status.PRESENT
        attendance.check_in_time = timezone.now()
        attendance.save()
        
        try:
            from trainings.models import Training
            
            training = Training.objects.filter(id=attendance.training_id).first()
            cpd_points = 0
            
            if training:
                if hasattr(training, 'cpd_points'):
                    cpd_points = training.cpd_points
                else:
                    if hasattr(training, 'duration') and training.duration:
                        if training.duration >= 2:
                            cpd_points = 1
                        if training.duration >= 4:
                            cpd_points = 2
                        if training.duration >= 6:
                            cpd_points = 3
            else:
                cpd_points = 1
            
            from cpd.models import CPD_Record
            
            cpd_record = CPD_Record.objects.create(
                id=uuid.uuid4(),
                points=cpd_points,
                earnedDate=timezone.now().date(),
                userId=user.id,
                training_id=attendance.training_id
            )
            
            cpd_record_created = True
            
        except ImportError as e:
            print(f"Warning: Could not import models for CPD calculation: {e}")
            cpd_points = 0
            cpd_record_created = False
        except Exception as e:
            print(f"Error creating CPD record: {e}")
            cpd_points = 0
            cpd_record_created = False
        
        response_data = {
            'success': True,
            'message': 'Check-in successful!',
            'attendance': {
                'id': str(attendance.id),
                'user_id': user.id,
                'username': user.username,
                'training_id': attendance.training_id,
                'status': attendance.status,
                'check_in_time': attendance.check_in_time,
                'date': attendance.date
            }
        }
        
        if cpd_record_created:
            response_data['cpd'] = {
                'points_earned': cpd_points,
                'record_created': True,
                'cpd_record_id': str(cpd_record.id) if 'cpd_record' in locals() else None
            }
        
        return Response(response_data)
        
    except Attendance.DoesNotExist:
        return Response({
            'success': False,
            'message': 'Attendance record does not exist'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_400_BAD_REQUEST)

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
            'date': att.date
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