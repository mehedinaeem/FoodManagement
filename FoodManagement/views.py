from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.db.models import Count
from logs.models import FoodLog
from inventory.models import InventoryItem


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
    Dashboard with user statistics, quick actions, and recommended resources.
    """
    user = request.user
    
    # Get user statistics
    total_logs = FoodLog.objects.filter(user=user).count()
    total_inventory = InventoryItem.objects.filter(user=user).count()
    fresh_inventory = InventoryItem.objects.filter(user=user, status='fresh').count()
    expiring_soon = InventoryItem.objects.filter(user=user, status='expiring_soon').count()
    
    # Recent logs (last 5)
    recent_logs = FoodLog.objects.filter(user=user).order_by('-date_consumed', '-created_at')[:5]
    
    # Recent inventory items (last 5)
    recent_inventory = InventoryItem.objects.filter(user=user).order_by('-created_at')[:5]
    
    # Get recommended resources using tracking logic
    from resources.tracking import TrackingAnalyzer
    analyzer = TrackingAnalyzer(user)
    recommended_resources = analyzer.get_recommendations(limit=3)
    
    # Check if user has seen welcome message (using session)
    show_welcome = request.session.get('show_welcome', True)
    if show_welcome:
        request.session['show_welcome'] = False
    
    context = {
        'user': user,
        'total_logs': total_logs,
        'total_inventory': total_inventory,
        'fresh_inventory': fresh_inventory,
        'expiring_soon': expiring_soon,
        'recent_logs': recent_logs,
        'recent_inventory': recent_inventory,
        'recommended_resources': recommended_resources,
        'show_welcome': show_welcome,
    }
    
    return render(request, 'dashboard_placeholder.html', context)

