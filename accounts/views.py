from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.models import User
from .forms import UserRegistrationForm, UserLoginForm, UserProfileUpdateForm


def register_view(request):
    """
    Handle user registration.
    """
    if request.user.is_authenticated:
        return redirect('dashboard_placeholder')
    
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, f'Account created successfully! Welcome, {user.username}!')
            login(request, user)
            return redirect('dashboard_placeholder')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = UserRegistrationForm()
    
    return render(request, 'accounts/register.html', {'form': form})


def login_view(request):
    """
    Handle user login.
    """
    if request.user.is_authenticated:
        return redirect('dashboard_placeholder')
    
    if request.method == 'POST':
        form = UserLoginForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f'Welcome back, {user.username}!')
            
            # Redirect to next page if specified, otherwise to dashboard
            next_url = request.GET.get('next', 'dashboard_placeholder')
            return redirect(next_url)
        else:
            messages.error(request, 'Invalid username or password.')
    else:
        form = UserLoginForm()
    
    return render(request, 'accounts/login.html', {'form': form})


@login_required
def logout_view(request):
    """
    Handle user logout.
    """
    logout(request)
    messages.info(request, 'You have been logged out successfully.')
    return redirect('accounts:login')


@login_required
def profile_view(request):
    """
    Display and update user profile.
    """
    user = request.user
    profile = user.profile
    
    if request.method == 'POST':
        form = UserProfileUpdateForm(request.POST, instance=profile, user=user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('accounts:profile')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = UserProfileUpdateForm(instance=profile, user=user)
    
    # Get user statistics
    from logs.models import FoodLog
    from inventory.models import InventoryItem
    
    total_logs = FoodLog.objects.filter(user=user).count()
    total_inventory = InventoryItem.objects.filter(user=user).count()
    fresh_inventory = InventoryItem.objects.filter(user=user, status='fresh').count()
    
    context = {
        'form': form,
        'profile': profile,
        'user': user,
        'total_logs': total_logs,
        'total_inventory': total_inventory,
        'fresh_inventory': fresh_inventory,
    }
    
    return render(request, 'accounts/profile.html', context)

