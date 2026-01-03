from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.http import require_GET
from django.contrib.auth import authenticate
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST, require_GET
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.http import HttpResponse
from .models import Attendance
from accounts.models import UserProfile
import json
import base64
import io
import time
import qrcode

@login_required
def trainer_training_list(request):
    print("=== DEBUG: trainer_training_list called ===")
    print(f"Request user: {request.user}")
    print(f"Is authenticated: {request.user.is_authenticated}")
    
    try:
        from training.models import Training
        print("=== DEBUG: Successfully imported Training model ===")
        
        all_trainings = Training.objects.all()
        print(f"=== DEBUG: Total trainings in DB: {all_trainings.count()}")
        
        for training in all_trainings:
            print(f"  - ID: {training.id}, Title: {training.title}, Trainer: {training.trainer}")
        
        trainings = Training.objects.filter(trainer=request.user)
        print(f"=== DEBUG: Trainings for user '{request.user.username}' (ID: {request.user.id}): {trainings.count()}")
            
        if trainings.count() == 0:
            print("=== DEBUG: User not authenticated, using all trainings")
            trainings = all_trainings
            
        trainings = Training.objects.filter(trainer=request.user)
        
        trainings = trainings.order_by('-date', '-time')
        
        today = timezone.now().date()
        
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
        
        print(f"=== DEBUG: Returning {len(data)} trainings from database")
        return JsonResponse({
            'success': True, 
            'trainings': data, 
            'source': 'database',
            'user_info': {
                'username': request.user.username,
                'id': request.user.id,
                'is_authenticated': request.user.is_authenticated
            }
        })
        
    except ImportError as e:
        print(f"=== DEBUG: ImportError occurred!")
        print(f"Error details: {e}")
        print(f"Error type: {type(e)}")
        
        try:
            print("=== DEBUG: Trying alternative import...")
            import importlib
            import sys
            
            print("Python path:")
            for path in sys.path:
                print(f"  - {path}")
            
            print("=== DEBUG: Looking for training module...")
            try:
                training_module = importlib.import_module('training')
                print(f"=== DEBUG: Found training module: {training_module}")
                if hasattr(training_module, 'models'):
                    print("=== DEBUG: training module has models attribute")
            except Exception as import_err:
                print(f"=== DEBUG: Cannot import training module: {import_err}")
                
        except Exception as debug_err:
            print(f"=== DEBUG: Error during debug: {debug_err}")
        
        data = [
            {
                'id': 1,
                'title': 'Python Programming Basics (Import Error)',
                'description': f'Cannot import Training model: {str(e)}',
                'date': timezone.now().date().isoformat(),
                'time': '09:00:00',
                'location': 'Main Campus',
                'cpd_points': 2,
                'status': 'ongoing',
            },
        ]
        return JsonResponse({
            'success': True, 
            'trainings': data,
            'source': 'simulated (ImportError)',
            'error': str(e),
            'error_type': 'ImportError'
        })
    
    except Exception as e:
        print(f"=== DEBUG: General Exception occurred!")
        print(f"Error: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        
        data = [
            {
                'id': 1,
                'title': 'Python Programming Basics (Error)',
                'description': f'Error: {type(e).__name__}: {str(e)}',
                'date': timezone.now().date().isoformat(),
                'time': '09:00:00',
                'location': 'Main Campus',
                'cpd_points': 2,
                'status': 'ongoing',
            },
        ]
        return JsonResponse({
            'success': True,
            'trainings': data,
            'source': 'simulated (Exception)',
            'error': str(e),
            'error_type': type(e).__name__,
            'message': f'Database error: {str(e)}'
        })

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
        
        from django.urls import reverse
        
        checkin_path = reverse('checkin_page')
        full_path = f"{checkin_path}?training_id={training_id}"
        
        current_scheme = 'https' if request.is_secure() else 'http'
        current_host = request.get_host()
        qr_url = f"{current_scheme}://{current_host}{full_path}"
        
        import socket
        hostname = socket.gethostname()
        local_ip = socket.gethostbyname(hostname)
        
        local_url = f"http://localhost:8000{full_path}"
        network_url = f"http://{local_ip}:8000{full_path}"
        
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(qr_url)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        
        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        buffer.seek(0)
        img_base64 = base64.b64encode(buffer.read()).decode()
        
        return JsonResponse({
            'success': True,
            'message': 'QR code generated',
            'training_id': training_id,
            'training_title': training_title,
            'qr_url': qr_url,
            'qr_url_local': local_url,
            'qr_url_network': network_url,
            'local_ip': local_ip,
            'qr_image': f"data:image/png;base64,{img_base64}",
            'expires_at': int(time.time()) + 3600,
            'expires_human': timezone.datetime.fromtimestamp(int(time.time()) + 3600).strftime('%Y-%m-%d %H:%M:%S')
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
        training_id = data.get('training_id', '').strip()
        
        if not all([username, password, training_id]):
            return JsonResponse({
                'success': False,
                'message': 'All fields are required'
            }, status=400)
        
        user = authenticate(request, username=username, password=password)
        if not user:
            return JsonResponse({
                'success': False,
                'message': 'Invalid credentials'
            }, status=401)
        
        try:
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
            
        except ImportError:
            print("Warning: UserProfile check skipped")
            
        try:
            from training.models import TrainingRegistration
            
            register_record = TrainingRegistration.objects.filter(
                employee=user,
                training_id=training_id
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
            training_id=training_id,
            status=Attendance.Status.PRESENT
        ).first()
        
        if existing:
            return JsonResponse({
                'success': False,
                'message': 'You have already checked in for this training'
            }, status=400)
            
        attendance = Attendance.objects.create(
            user=user,
            training_id=training_id,
            status=Attendance.Status.PRESENT,
            check_in_time=timezone.now(),
        )
        
        cpd_created = False
        cpd_points = 0
        
        try:
            from training.models import Training
            from cpd.models import CPDRecord
            
            try:
                training_id_int = int(training_id)
            except ValueError:
                training_id_int = training_id
                
            training = Training.objects.filter(id=training_id_int).first()
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
            
        except ImportError:
            print("Warning: CPD calculation skipped")
            
        response_data = {
            'success': True,
            'message': 'Check-in successful!',
            'attendance': {
                'id': str(attendance.id),
                'user_id': user.id,
                'username': user.username,
                'training_id': training_id,
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
 
@require_GET     
def get_checkin_info(request, attendance_id):
    try:
        attendance = get_object_or_404(Attendance, id=attendance_id)
        
        time_diff = timezone.now() - attendance.date
        if time_diff.total_seconds() > 3600:
            return JsonResponse({
                'success': False,
                'message': 'QR code has expired',
                'status': 'Expired'
            })
        
        if attendance.user:
            return JsonResponse({
                'success': False,
                'message': 'Already checked in',
                'status': 'Used'
            })
        
        training_info = None
        try:
            from training.models import Training
            training = Training.objects.filter(id=attendance.training_id).first()
            if training:
                training_info = {
                    'id': training.id,
                    'title': training.title,
                    'date': training.date.isoformat() if training.date else None,
                    'time': str(training.time) if training.time else None,
                    'location': training.location,
                    'cpd_points': training.cpd_points,
                }
        except ImportError:
            pass
        
        return JsonResponse({
            'success': True,
            'attendance_id': str(attendance.id),
            'training_info': training_info,
            'status': 'Valid',
            'expires_in': max(0, 3600 - int(time_diff.total_seconds()))
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e),
            'status': 'Error'
        }, status=500)
        
def checkin_page_view(request):
    training_id = request.GET.get('training_id', '')
    
    training_info = None
    if training_id:
        try:
            from training.models import Training
            training = Training.objects.filter(id=training_id).first()
            if training:
                training_info = {
                    'title': training.title,
                    'date': training.date,
                    'time': training.time,
                    'location': training.location,
                    'trainer_name': training.trainer.get_full_name() or training.trainer.username,
                }
        except ImportError:
            pass
    
    return render(request, 'attendance/checkin_page.html', {
        'training_id': training_id,
        'training_info': training_info,
    })        
        
@login_required
def trainer_attendance_view(request):
    try:
        from training.models import Training
        
        trainings = Training.objects.filter(trainer=request.user).order_by('-date', '-time')
        
        training_data = []
        for training in trainings:
            attendances = Attendance.objects.filter(training_id=str(training.id))
            
            present_count = attendances.filter(status=Attendance.Status.PRESENT).count()
            absent_count = attendances.filter(status=Attendance.Status.ABSENT).count()
            total_count = attendances.count()
            
            try:
                from training.models import TrainingRegistration
                registered_users = TrainingRegistration.objects.filter(
                    training_id=training.id,
                    status='Approved'
                ).count()
                
                not_checked_in = max(0, registered_users - present_count)
            except ImportError:
                not_checked_in = 0
            
            training_data.append({
                'id': training.id,
                'title': training.title,
                'date': training.date,
                'time': training.time,
                'location': training.location,
                'total_attendance': total_count,
                'present_count': present_count,
                'absent_count': absent_count,
                'not_checked_in': not_checked_in,
                'status': 'upcoming' if training.date > timezone.now().date() else 
                         'ongoing' if training.date == timezone.now().date() else 
                         'completed',
            })
        
        total_trainings = len(training_data)
        total_present = sum(t['present_count'] for t in training_data)
        total_absent = sum(t['absent_count'] for t in training_data)
        
        return render(request, 'attendance/trainer_attendance.html', {
            'trainings': training_data,
            'total_trainings': total_trainings,
            'total_present': total_present,
            'total_absent': total_absent,
            'current_date': timezone.now().date(),
            'user_role': 'trainer',
        })
        
    except Exception as e:
        print(f"Error in trainer_attendance_view: {str(e)}")
        return render(request, 'attendance/trainer_attendance.html', {
            'error': str(e),
            'trainings': [],
            'total_trainings': 0,
            'total_present': 0,
            'total_absent': 0,
            'current_date': timezone.now().date(),
            'user_role': 'trainer',
        })