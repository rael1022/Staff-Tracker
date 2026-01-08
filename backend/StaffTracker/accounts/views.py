from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from .models import UserProfile
from django.contrib.auth.models import Group
from django.contrib.auth import authenticate, login
from django.shortcuts import render, redirect
from .models import UserProfile
from django.contrib import messages
from department.models import Department

ROLE_DEPARTMENTS = {
    'Employee': ['IT', 'Finance', 'Marketing', 'Risk Management', 'Customer Support', 'Legal'],
    'Trainer': ['IT', 'Finance', 'Marketing', 'Risk Management', 'Customer Support', 'Legal'],
    'HOD': ['IT', 'Finance', 'Marketing', 'Risk Management', 'Customer Support', 'Legal'],
    'HR': [],  
}

def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)

        if user is not None:
            if user.is_superuser:
                login(request, user)
                return redirect('/dashboard/')
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
    selected_role = None
    departments = Department.objects.none()
    department_value = None

    if request.method == "POST" and 'role' in request.POST and 'username' not in request.POST:
        selected_role = request.POST.get("role")
        if selected_role == "HR":
            departments = Department.objects.none()
        elif selected_role:
            allowed_dept_names = ROLE_DEPARTMENTS.get(selected_role, [])
            departments = Department.objects.filter(name__in=allowed_dept_names)
        else:
            departments = Department.objects.all()

    if request.method == "POST" and 'username' in request.POST:
        selected_role = request.POST.get("role")
        department_value = request.POST.get("department")

        username = request.POST['username'].strip()
        email = request.POST['email'].strip()
        password = request.POST['password'].strip()
        extra_info = request.POST.get('extra_info', '')

        if User.objects.filter(username=username).exists():
            if selected_role == "HR":
                departments = Department.objects.none()
            elif selected_role:
                allowed_dept_names = ROLE_DEPARTMENTS.get(selected_role, [])
                departments = Department.objects.filter(name__in=allowed_dept_names)
            else:
                departments = Department.objects.all()

            return render(request, "register/register.html", {
                "error": "Username already exists",
                "selected_role": selected_role,
                "departments": departments,
                "department_value": department_value
            })

        department = None
        if selected_role != "HR" and department_value:
            department = get_object_or_404(Department, id=department_value)

        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            is_active=False
        )

        profile = UserProfile.objects.create(
            user=user,
            role=selected_role,
            department=department,
            extra_info=extra_info,
            is_approved=False
        )

        if selected_role:
            group, _ = Group.objects.get_or_create(name=selected_role)
            user.groups.add(group)

        if selected_role == "HR":
            departments = Department.objects.none()
        elif selected_role:
            allowed_dept_names = ROLE_DEPARTMENTS.get(selected_role, [])
            departments = Department.objects.filter(name__in=allowed_dept_names)
        else:
            departments = Department.objects.all()

        return render(request, "register/register.html", {
            "message": "Register Successful. Awaiting HR approval.",
            "selected_role": '',   
            "departments": Department.objects.none(),  
            "department_value": ''  ,
            "request": {"POST": {"username": "", "email": ""}} 
        })

    return render(request, "register/register.html", {
        "selected_role": selected_role,
        "departments": departments,
        "department_value": department_value
    })

@login_required
def hr_create_user(request):
    if not request.user.groups.filter(name='HR').exists():
        return redirect('/dashboard/')

    roles = list(ROLE_DEPARTMENTS.keys())
    selected_role = request.POST.get('role', None)
    departments = Department.objects.filter(name__in=ROLE_DEPARTMENTS.get(selected_role, [])) if selected_role else Department.objects.none()

    context = {
        'roles': roles,
        'departments': departments,
        'selected_role': selected_role,
        'message': '',
        'error': '',
    }

    action = request.POST.get('action', None)

    if request.method == 'POST' and action == 'submit':
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '').strip()
        role = request.POST.get('role')
        department_id = request.POST.get('department')

        if not username or not email or not password or not role:
            context['error'] = "Username, email, password, and role are required."
            return render(request, 'manage_account/create_user.html', context)

        if User.objects.filter(username=username).exists():
            context['error'] = "Username already exists."
            return render(request, 'manage_account/create_user.html', context)

        user = User.objects.create_user(username=username, email=email, password=password)

        department = None
        if role != "HR" and department_id:
            department = get_object_or_404(Department, id=department_id)

        profile = UserProfile.objects.create(
            user=user,
            role=role,
            department=department,
            is_approved=True
        )

        group, _ = Group.objects.get_or_create(name=role)
        user.groups.add(group)

        context['message'] = "User created successfully."
        context['departments'] = Department.objects.filter(name__in=ROLE_DEPARTMENTS.get(role, []))
        context['selected_role'] = role

    return render(request, 'manage_account/create_user.html', context)

@login_required
def hr_update_user(request, user_id):
    if not request.user.groups.filter(name='HR').exists():
        return redirect('/dashboard/')

    user = get_object_or_404(User, id=user_id)
    profile = user.userprofile

    roles = list(ROLE_DEPARTMENTS.keys())
    selected_role = request.POST.get('role', profile.role)

    allowed_dept_names = ROLE_DEPARTMENTS.get(selected_role, [])
    departments = Department.objects.filter(name__in=allowed_dept_names)

    context = {
        'edit_user': user,
        'roles': roles,
        'departments': departments,
        'selected_role': selected_role,
        'role_departments': ROLE_DEPARTMENTS,
        'message': '',
        'error': '',
    }

    action = request.POST.get('action', 'submit')

    if request.method == 'POST' and action == 'submit':
        new_username = request.POST.get('username', '').strip()
        new_email = request.POST.get('email', '').strip()
        role = request.POST.get('role')
        department_id = request.POST.get('department')

        if not new_username or not new_email:
            context['error'] = "Username and email are required."
            return render(request, 'manage_account/update_user.html', context)

        if User.objects.filter(username=new_username).exclude(id=user.id).exists():
            context['error'] = "Username already exists."
            return render(request, 'manage_account/update_user.html', context)

        user.username = new_username
        user.email = new_email
        user.groups.clear()
        group, _ = Group.objects.get_or_create(name=role)
        user.groups.add(group)

        profile.role = role
        if role == 'HR':
            profile.department = None
        else:
            profile.department = Department.objects.get(id=department_id)

        user.save()
        profile.save()

        messages.success(request, "User updated successfully.")
        return redirect('/dashboard/')

    return render(request, 'manage_account/update_user.html', context)

@login_required
def hr_delete_user(request, user_id):
    if not request.user.groups.filter(name='HR').exists():
        return redirect('/dashboard/')

    user = get_object_or_404(User, id=user_id)
    if request.method == 'POST':
        user.delete()
        return redirect('/dashboard/')

@login_required
def hr_toggle_user(request, user_id):
    if not request.user.groups.filter(name='HR').exists():
        return redirect('/dashboard/')

    user = User.objects.get(id=user_id)
    user.is_active = not user.is_active
    user.save()

    return redirect('/dashboard/')

@login_required
def hr_manage_users(request):
    if not request.user.groups.filter(name='HR').exists():
        return redirect('/dashboard/')

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'approve':
            approve_id = request.POST.get('approve_id')
            try:
                profile = UserProfile.objects.get(user__id=approve_id)
                profile.is_approved = True
                profile.save()

                user = profile.user
                user.is_active = True
                user.save()

                role = profile.role
                group, _ = Group.objects.get_or_create(name=role)
                user.groups.clear()
                user.groups.add(group)

            except UserProfile.DoesNotExist:
                pass

        elif action == 'reject':
            reject_id = request.POST.get('reject_id')
            try:
                user = User.objects.get(id=reject_id)
                user.delete()
            except User.DoesNotExist:
                pass

    pending_users = UserProfile.objects.filter(is_approved=False)
    all_users = User.objects.filter(userprofile__is_approved=True)

    return render(
        request,
        'manage_account/hr_user_management.html',
        {
            'pending_users': pending_users,
            'all_users': all_users,
        }
    )

@login_required
def dashboard(request):
    user = request.user

    if user.groups.filter(name='HR').exists():
        return render(request, 'dashboard/hr_dashboard.html')

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
