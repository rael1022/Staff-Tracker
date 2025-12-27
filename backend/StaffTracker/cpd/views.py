from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import CPDRecord

# Create your views here.
@login_required
def my_cpd(request):
    records = CPDRecord.objects.filter(user=request.user)
    total_points = sum(r.points for r in records)
    return render(request, 'cpd/my_cpd.html', {
        'records': records,
        'total_points': total_points
    })