from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from .models import UserProfile
from django.contrib.auth.models import Group
from django.contrib.auth import authenticate, login
from django.shortcuts import render, redirect
from .models import UserProfile

def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)

        if user is not None:
            try:
                profile = user.userprofile  
                if not profile.is_approved:
                    return render(request, 'login/login.html', {'error': 'You must be approved by an admin before logging in.'})
            except UserProfile.DoesNotExist:
                return render(request, 'login/login.html', {'error': 'User profile does not exist.'})

            login(request, user)
            return redirect('/dashboard/')
        else:
            return render(request, 'login/login.html', {'error': 'Invalid username or password.'})
    
    return render(request, 'login/login.html')

def register_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        email = request.POST['email']
        password = request.POST['password']
        role = request.POST.get('role') 
        extra_info = request.POST['extra_info']

        if User.objects.filter(username=username).exists():
            return render(request, 'register/register.html', {'error': 'username exists'})
        
        user = User.objects.create_user(username=username, email=email, password=password)
        UserProfile.objects.create(user=user, role=role, extra_info=extra_info)

        return render(request, 'register/register.html', {'message': 'Register Successful'})
    
    return render(request, 'register/register.html')

@login_required
def hr_create_user(request):
    if not request.user.groups.filter(name='HR').exists():
        return redirect('/dashboard/')

    if request.method == 'POST':
        username = request.POST['username']
        email = request.POST['email']
        password = request.POST['password']
        role = request.POST['role']

        user = User.objects.create_user(
            username=username,
            email=email,
            password=password
        )

        UserProfile.objects.create(
            user=user,
            role=role,
            is_approved=True
        )

        group, _ = Group.objects.get_or_create(name=role)
        user.groups.add(group)

        return redirect('/dashboard/')

    return render(request, 'manage_account/create_user.html')

from django.contrib import messages

@login_required
def hr_update_user(request, user_id):
    if not request.user.groups.filter(name='HR').exists():
        return redirect('/dashboard/')

    user = get_object_or_404(User, id=user_id)
    profile = user.userprofile

    if request.method == 'POST':
        new_username = request.POST['username']
        new_email = request.POST['email']
        role = request.POST['role']

        # 检查用户名是否重复
        if User.objects.filter(username=new_username).exclude(id=user.id).exists():
            messages.error(request, "Username already exists. Please choose a different one.")
            return render(request, 'manage_account/update_user.html', {'edit_user': user})

        # 更新 User
        user.username = new_username
        user.email = new_email

        # 更新 Group
        user.groups.clear()
        group, _ = Group.objects.get_or_create(name=role)
        user.groups.add(group)

        # 更新 UserProfile role
        profile.role = role

        user.save()
        profile.save()

        messages.success(request, "User updated successfully.")
        return redirect('/dashboard/')

    return render(request, 'manage_account/update_user.html', {'edit_user': user})



@login_required
def hr_toggle_user(request, user_id):
    if not request.user.groups.filter(name='HR').exists():
        return redirect('/dashboard/')

    user = User.objects.get(id=user_id)
    user.is_active = not user.is_active
    user.save()

    return redirect('/dashboard/')

@login_required
def dashboard(request):
    user = request.user

    if user.groups.filter(name='HR').exists():

        if request.method == 'POST':
            approve_id = request.POST.get('approve_id')

            try:
                profile = UserProfile.objects.get(user__id=approve_id)

                profile.is_approved = True
                profile.save()

                role = profile.role  

                group, _ = Group.objects.get_or_create(name=role)

                approved_user = profile.user
                approved_user.groups.clear()
                approved_user.groups.add(group)

            except UserProfile.DoesNotExist:
                pass

        pending_users = UserProfile.objects.filter(is_approved=False)
        all_users = User.objects.exclude(is_superuser=True)

        return render(
            request,
            'dashboard/hr_dashboard.html',
            {
                'pending_users': pending_users,
                'all_users': all_users
            }
        )


    elif user.groups.filter(name='HOD').exists():
        return render(request, 'dashboard/hod_dashboard.html')

    elif user.groups.filter(name='Trainer').exists():
        return render(request, 'dashboard/trainer_dashboard.html')

    else:
        return render(request, 'dashboard/employee_dashboard.html')
   
@login_required
def toggle_user_status(request, user_id):
    if not request.user.groups.filter(name='HR').exists():
        return redirect('/dashboard/')

    user = User.objects.get(id=user_id)
    user.is_active = not user.is_active
    user.save()

    return redirect('/dashboard/')
