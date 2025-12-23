from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required

# Create your views here.
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

def login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('/dashboard/')
        else:
            return render(request, 'login/login.html', {'error': 'Wrong password'})
    return render(request, 'login/login.html')