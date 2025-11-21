from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required


def home_view(request):
    """
    Home page - redirects authenticated users to dashboard, shows landing page for others.
    """
    if request.user.is_authenticated:
        return redirect('dashboard_placeholder')
    return render(request, 'landing.html')


@login_required
def dashboard_placeholder(request):
    """
    Temporary dashboard placeholder until dashboard app is created.
    """
    return render(request, 'dashboard_placeholder.html', {
        'user': request.user,
    })

