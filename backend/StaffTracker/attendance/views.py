from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse, HttpResponseBadRequest
from django.contrib.auth import authenticate
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST, require_GET
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from .models import Attendance
import json
import qrcode
import base64
import io
import time

@login_required
def trainer_training_list(request):
    try:
        from training.models import Training
        
        trainings = Training.objects.filter(trainer=request.user)
        trainings = trainings.order_by('-date', '-time')
        
        today = timezone.now().date()
        
        context = {
            'trainings': trainings,
            'open_trainings': trainings.filter(date__gt=today).count(),
            'ongoing_trainings': trainings.filter(date=today).count(),
            'completed_trainings': trainings.filter(date__lt=today).count(),
            'total_trainings': trainings.count(),
            'now': today,
        }
        
        data = []
        for training in trainings:
            data.append({
                'id': training.id,
                'title': training.title,
                'description': training.description,
                'date': training.date.isoformat() if training.date else None,
                'time': str(training.time) if training.time else None,
                'location': training.location,
                'cpd_points': training.cpd_points,
                'status': 'upcoming' if training.date > today else 
                         'ongoing' if training.date == today else 
                         'completed',
            })
        
        return JsonResponse({'success': True, 'trainings': data})
        
    except ImportError:
        trainings = [
            {
                'id': 1,
                'title': 'Python Programming Basics',
                'description': 'Learn Python fundamentals',
                'date': timezone.now().date(),
                'time': '09:00:00',
                'location': 'Main Campus',
                'trainer': request.user,
                'cpd_points': 2,
            },
        ]

@require_POST
@login_required
@csrf_exempt  
def generate_qr_code(request):
    try:
        data = json.loads(request.body)
        training_id = data.get('training_id')
        training_title = data.get('training_title', 'Training')
        
        if not training_id:
            return JsonResponse({
                'success': False,
                'message': 'training_id is required'
            }, status=400)
        
        attendance = Attendance.objects.create(
            training_id=str(training_id),
            status=Attendance.Status.ABSENT,
            date=timezone.now().date(),
        )
        
        qr_data = {
            "type": "attendance_checkin",
            "training_id": str(training_id),
            "training_title": training_title,
            "attendance_id": str(attendance.id),
            "timestamp": int(time.time()),
            "expires": int(time.time()) + 3600,
            "message": f"Scan to check in for: {training_title}"
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
        
        return JsonResponse({
            'success': True,
            'message': 'QR code generated',
            'attendance_id': str(attendance.id),
            'training_id': training_id,
            'training_title': training_title,
            'qr_data': qr_json,
            'qr_image': f"data:image/png;base64,{img_base64}",
            'expires_at': qr_data['expires'],
            'expires_human': timezone.datetime.fromtimestamp(qr_data['expires']).strftime('%Y-%m-%d %H:%M:%S')
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=500)

@login_required
def get_training_attendance(request, training_id):
    try:
        attendances = Attendance.objects.filter(training_id=training_id)
        
        data = []
        for att in attendances:
            user_info = None
            if att.user:
                try:
                    from registration.models import UserProfile
                    user_profile = UserProfile.objects.get(user=att.user)
                    user_info = {
                        'id': att.user.id,
                        'username': att.user.username,
                        'full_name': f"{att.user.first_name} {att.user.last_name}".strip() or att.user.username,
                        'role': user_profile.role,
                        'is_approved': user_profile.is_approved,
                    }
                except:
                    user_info = {
                        'id': att.user.id,
                        'username': att.user.username,
                        'full_name': att.user.username,
                        'role': 'Unknown',
                        'is_approved': False,
                    }
            
            data.append({
                'id': str(att.id),
                'user': user_info,
                'status': att.status,
                'check_in_time': att.check_in_time.isoformat() if att.check_in_time else None,
                'date': att.date.isoformat(),
                'is_qr_checkin': bool(att.check_in_time),
            })
        
        training_info = None
        try:
            from training.models import Training
            training = Training.objects.filter(id=training_id).first()
            if training:
                training_info = {
                    'id': training.id,
                    'title': training.title,
                    'date': training.date.isoformat() if training.date else None,
                    'location': training.location,
                }
        except ImportError:
            pass
        
        return JsonResponse({
            'success': True,
            'training_id': training_id,
            'training_info': training_info,
            'total': attendances.count(),
            'present': attendances.filter(status=Attendance.Status.PRESENT).count(),
            'absent': attendances.filter(status=Attendance.Status.ABSENT).count(),
            'attendances': data
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=500)
        
@require_POST
@login_required
@csrf_exempt
def manual_checkin(request):
    try:
        data = json.loads(request.body)
        training_id = data.get('training_id')
        user_id = data.get('user_id')
        
        if not all([training_id, user_id]):
            return JsonResponse({
                'success': False,
                'message': 'training_id and user_id are required'
            }, status=400)
        
        from django.contrib.auth.models import User
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'User not found'
            }, status=404)
        
        existing = Attendance.objects.filter(
            user=user,
            training_id=training_id,
            status=Attendance.Status.PRESENT
        ).first()
        
        if existing:
            return JsonResponse({
                'success': False,
                'message': 'User already checked in for this training'
            }, status=400)
        
        try:
            from training.models import TrainingRegistration
            register_record = TrainingRegistration.objects.filter(
                employee=user,
                training_id=training_id
            ).first()
            
            if not register_record:
                return JsonResponse({
                    'success': False,
                    'message': 'User is not registered for this training'
                }, status=403)
            
            if register_record.status != 'Approved':
                return JsonResponse({
                    'success': False,
                    'message': 'User registration is not approved'
                }, status=403)
                
        except ImportError:
            print("Warning: TrainingRegistration check skipped")
        
        attendance = Attendance.objects.create(
            user=user,
            training_id=str(training_id),
            status=Attendance.Status.PRESENT,
            check_in_time=timezone.now(),
            date=timezone.now().date(),
        )
        
        cpd_created = False
        cpd_points = 0
        
        try:
            from training.models import Training
            from cpd.models import CPDRecord
            
            training = Training.objects.filter(id=training_id).first()
            if training and hasattr(training, 'cpd_points'):
                cpd_points = training.cpd_points
            else:
                cpd_points = 1
            
            cpd_record = CPDRecord.objects.create(
                user=user,
                training_id=training_id,
                points=cpd_points,
                earned_date=timezone.now().date()
            )
            cpd_created = True
            cpd_record_id = str(cpd_record.id)
            
        except ImportError:
            print("Warning: CPD calculation skipped")
        
        response_data = {
            'success': True,
            'message': 'Manual check-in successful',
            'attendance': {
                'id': str(attendance.id),
                'user_id': user.id,
                'username': user.username,
                'training_id': training_id,
                'check_in_time': attendance.check_in_time.isoformat(),
                'date': attendance.date.isoformat(),
                'is_manual': True,
            }
        }
        
        if cpd_created:
            response_data['cpd'] = {
                'points_earned': cpd_points,
                'record_created': True,
            }
        
        return JsonResponse(response_data)
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=500)

@require_POST
@csrf_exempt
def qr_checkin(request):
    try:
        data = json.loads(request.body)
        
        username = data.get('username', '').strip()
        password = data.get('password', '').strip()
        attendance_id = data.get('attendance_id', '').strip()
        
        if not all([username, password, attendance_id]):
            return JsonResponse({
                'success': False,
                'message': 'All fields are required'
            }, status=400)
        
        try:
            attendance = Attendance.objects.get(id=attendance_id)
        except Attendance.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'QR code invalid or expired'
            }, status=404)
        
        try:
            qr_data = json.loads(attendance.training_id)
            if 'expires' in qr_data and qr_data['expires'] < int(time.time()):
                return JsonResponse({
                    'success': False,
                    'message': 'QR code has expired'
                }, status=400)
        except:
            pass
        
        if attendance.user:
            return JsonResponse({
                'success': False,
                'message': 'This QR code has already been used'
            }, status=400)
        
        user = authenticate(request, username=username, password=password)
        if not user:
            return JsonResponse({
                'success': False,
                'message': 'Invalid credentials'
            }, status=401)
        
        try:
            from registration.models import UserProfile
            user_profile = UserProfile.objects.get(user=user)
            
            if user_profile.role != 'Employee':
                return JsonResponse({
                    'success': False,
                    'message': 'Only employees can check in'
                }, status=403)
            
            if not user_profile.is_approved:
                return JsonResponse({
                    'success': False,
                    'message': 'Your account is not approved'
                }, status=403)
                
        except UserProfile.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'User profile not found'
            }, status=400)
        except ImportError:
            print("Warning: UserProfile check skipped")
        
        try:
            from training.models import TrainingRegistration
            
            register_record = TrainingRegistration.objects.filter(
                employee=user,
                training_id=attendance.training_id
            ).first()
            
            if not register_record:
                return JsonResponse({
                    'success': False,
                    'message': 'You are not registered for this training'
                }, status=403)
            
            if register_record.status != 'Approved':
                return JsonResponse({
                    'success': False,
                    'message': 'Your registration is pending approval'
                }, status=403)
                
        except ImportError:
            print("Warning: TrainingRegistration check skipped")
        
        existing = Attendance.objects.filter(
            user=user,
            training_id=attendance.training_id,
            status=Attendance.Status.PRESENT
        ).exclude(id=attendance_id).first()
        
        if existing:
            return JsonResponse({
                'success': False,
                'message': 'You have already checked in'
            }, status=400)
        
        attendance.user = user
        attendance.status = Attendance.Status.PRESENT
        attendance.check_in_time = timezone.now()
        attendance.save()
        
        cpd_created = False
        cpd_points = 0
        
        try:
            from training.models import Training
            from cpd.models import CPDRecord
            
            training = Training.objects.filter(id=attendance.training_id).first()
            if training and hasattr(training, 'cpd_points'):
                cpd_points = training.cpd_points
            else:
                cpd_points = 1
            
            cpd_record = CPDRecord.objects.create(
                user=user,
                training_id=attendance.training_id,
                points=cpd_points,
                earned_date=timezone.now().date()
            )
            cpd_created = True
            
        except ImportError:
            print("Warning: CPD calculation skipped")
        
        response_data = {
            'success': True,
            'message': 'Check-in successful!',
            'attendance': {
                'id': str(attendance.id),
                'user_id': user.id,
                'username': user.username,
                'training_id': attendance.training_id,
                'check_in_time': attendance.check_in_time.isoformat(),
                'date': attendance.date.isoformat(),
                'is_qr': True,
            }
        }
        
        if cpd_created:
            response_data['cpd'] = {
                'points_earned': cpd_points,
                'record_created': True,
            }
        
        return JsonResponse(response_data)
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'message': 'Invalid data format'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error: {str(e)}'
        }, status=500)

