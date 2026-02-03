# accounts/views.py 또는 프로젝트 views.py
from django.shortcuts import render
from django.contrib.auth.decorators import login_required

@login_required
def main_view(request):
    return render(request, "main.html")