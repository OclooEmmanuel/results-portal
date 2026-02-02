from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required

# Create your views here.
def register_view(request):
    pass


def admin_login(request):

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)

        if user is not None and user.is_staff:
            login(request, user)
            messages.success(request,'welcome! Admin ')
            return redirect('manage_results')

        messages.error(request, 'Invalid credntials or not Authorized.')
    return render(request, 'admin_login.html')


@login_required
def admin_logout(request):
    logout(request)
    messages.success(request, "Logged out successfully")
    return redirect("check_results")
