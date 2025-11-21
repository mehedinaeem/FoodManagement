from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum, Count
from django.utils import timezone
from datetime import timedelta
from .models import FoodLog
from .forms import FoodLogForm, FoodLogFilterForm


@login_required
def log_list(request):
    """
    Display list of food logs with filtering options.
    """
    logs = FoodLog.objects.filter(user=request.user)
    filter_form = FoodLogFilterForm(request.GET)
    
    # Apply filters
    if filter_form.is_valid():
        category = filter_form.cleaned_data.get('category')
        date_from = filter_form.cleaned_data.get('date_from')
        date_to = filter_form.cleaned_data.get('date_to')
        
        if category:
            logs = logs.filter(category=category)
        if date_from:
            logs = logs.filter(date_consumed__gte=date_from)
        if date_to:
            logs = logs.filter(date_consumed__lte=date_to)
    
    # Statistics
    total_logs = logs.count()
    today_logs = logs.filter(date_consumed=timezone.now().date()).count()
    week_logs = logs.filter(
        date_consumed__gte=timezone.now().date() - timedelta(days=7)
    ).count()
    
    # Category breakdown
    category_stats = logs.values('category').annotate(
        count=Count('id')
    ).order_by('-count')
    
    context = {
        'logs': logs[:50],  # Limit to 50 most recent
        'filter_form': filter_form,
        'total_logs': total_logs,
        'today_logs': today_logs,
        'week_logs': week_logs,
        'category_stats': category_stats,
    }
    
    return render(request, 'logs/list.html', context)


@login_required
def log_create(request):
    """
    Create a new food log entry.
    """
    if request.method == 'POST':
        form = FoodLogForm(request.POST)
        if form.is_valid():
            log = form.save(commit=False)
            log.user = request.user
            log.save()
            messages.success(request, f'Food log for "{log.item_name}" created successfully!')
            return redirect('logs:list')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = FoodLogForm()
    
    return render(request, 'logs/form.html', {
        'form': form,
        'title': 'Log Food Consumption',
        'action': 'Create'
    })


@login_required
def log_edit(request, pk):
    """
    Edit an existing food log entry.
    """
    log = get_object_or_404(FoodLog, pk=pk, user=request.user)
    
    if request.method == 'POST':
        form = FoodLogForm(request.POST, instance=log)
        if form.is_valid():
            form.save()
            messages.success(request, f'Food log for "{log.item_name}" updated successfully!')
            return redirect('logs:list')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = FoodLogForm(instance=log)
    
    return render(request, 'logs/form.html', {
        'form': form,
        'log': log,
        'title': 'Edit Food Log',
        'action': 'Update'
    })


@login_required
def log_delete(request, pk):
    """
    Delete a food log entry.
    """
    log = get_object_or_404(FoodLog, pk=pk, user=request.user)
    
    if request.method == 'POST':
        item_name = log.item_name
        log.delete()
        messages.success(request, f'Food log for "{item_name}" deleted successfully!')
        return redirect('logs:list')
    
    return render(request, 'logs/delete.html', {'log': log})


@login_required
def log_detail(request, pk):
    """
    View details of a food log entry.
    """
    log = get_object_or_404(FoodLog, pk=pk, user=request.user)
    return render(request, 'logs/detail.html', {'log': log})


@login_required
def log_history(request):
    """
    Display consumption history with statistics.
    """
    logs = FoodLog.objects.filter(user=request.user)
    
    # Date range filter
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    
    if date_from:
        logs = logs.filter(date_consumed__gte=date_from)
    if date_to:
        logs = logs.filter(date_consumed__lte=date_to)
    
    # Statistics
    total_items = logs.count()
    unique_items = logs.values('item_name').distinct().count()
    
    # Daily consumption
    daily_consumption = logs.values('date_consumed').annotate(
        count=Count('id')
    ).order_by('-date_consumed')[:30]  # Last 30 days
    
    # Category breakdown
    category_breakdown = logs.values('category').annotate(
        count=Count('id')
    ).order_by('-count')
    
    context = {
        'logs': logs[:100],  # Limit to 100
        'total_items': total_items,
        'unique_items': unique_items,
        'daily_consumption': daily_consumption,
        'category_breakdown': category_breakdown,
    }
    
    return render(request, 'logs/history.html', context)
