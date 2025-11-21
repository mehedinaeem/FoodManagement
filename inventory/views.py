from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count, Q
from django.utils import timezone
from datetime import timedelta
from .models import InventoryItem, FoodItem
from .forms import InventoryItemForm, InventoryFilterForm, FoodItemFilterForm


@login_required
def inventory_list(request):
    """
    Display list of inventory items with filtering options.
    """
    items = InventoryItem.objects.filter(user=request.user)
    filter_form = InventoryFilterForm(request.GET)
    
    # Apply filters
    if filter_form.is_valid():
        category = filter_form.cleaned_data.get('category')
        status = filter_form.cleaned_data.get('status')
        
        if category:
            items = items.filter(category=category)
        if status:
            items = items.filter(status=status)
    
    # Update statuses for all items
    for item in items:
        item.update_status()
    
    # Statistics
    total_items = items.count()
    fresh_items = items.filter(status='fresh').count()
    expiring_soon = items.filter(status='expiring_soon').count()
    expired_items = items.filter(status='expired').count()
    
    # Category breakdown
    category_stats = items.values('category').annotate(
        count=Count('id')
    ).order_by('-count')
    
    # Items expiring soon (next 3 days)
    expiring_items = items.filter(
        expiration_date__gte=timezone.now().date(),
        expiration_date__lte=timezone.now().date() + timedelta(days=3)
    ).exclude(status='consumed')[:10]
    
    # Get AI expiration risk predictions
    from ai_analytics.expiration_predictor import ExpirationRiskPredictor
    expiration_predictor = ExpirationRiskPredictor(request.user)
    expiration_alerts = expiration_predictor.get_high_risk_alerts(limit=5)
    
    context = {
        'items': items,
        'filter_form': filter_form,
        'total_items': total_items,
        'fresh_items': fresh_items,
        'expiring_soon': expiring_soon,
        'expired_items': expired_items,
        'category_stats': category_stats,
        'expiring_items': expiring_items,
        'expiration_alerts': expiration_alerts,
    }
    
    return render(request, 'inventory/list.html', context)


@login_required
def inventory_create(request):
    """
    Create a new inventory item.
    """
    if request.method == 'POST':
        form = InventoryItemForm(request.POST)
        if form.is_valid():
            item = form.save(commit=False)
            item.user = request.user
            item.update_status()  # Set initial status
            item.save()
            messages.success(request, f'"{item.item_name}" added to inventory successfully!')
            return redirect('inventory:list')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = InventoryItemForm()
    
    return render(request, 'inventory/form.html', {
        'form': form,
        'title': 'Add Inventory Item',
        'action': 'Add'
    })


@login_required
def inventory_edit(request, pk):
    """
    Edit an existing inventory item.
    """
    item = get_object_or_404(InventoryItem, pk=pk, user=request.user)
    
    if request.method == 'POST':
        form = InventoryItemForm(request.POST, instance=item)
        if form.is_valid():
            item = form.save()
            item.update_status()  # Update status based on expiration
            messages.success(request, f'"{item.item_name}" updated successfully!')
            return redirect('inventory:list')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = InventoryItemForm(instance=item)
    
    return render(request, 'inventory/form.html', {
        'form': form,
        'item': item,
        'title': 'Edit Inventory Item',
        'action': 'Update'
    })


@login_required
def inventory_delete(request, pk):
    """
    Delete an inventory item.
    """
    item = get_object_or_404(InventoryItem, pk=pk, user=request.user)
    
    if request.method == 'POST':
        item_name = item.item_name
        item.delete()
        messages.success(request, f'"{item_name}" removed from inventory successfully!')
        return redirect('inventory:list')
    
    return render(request, 'inventory/delete.html', {'item': item})


@login_required
def inventory_detail(request, pk):
    """
    View details of an inventory item.
    """
    item = get_object_or_404(InventoryItem, pk=pk, user=request.user)
    item.update_status()  # Ensure status is up to date
    return render(request, 'inventory/detail.html', {'item': item})


@login_required
def inventory_mark_consumed(request, pk):
    """
    Mark an inventory item as consumed and create a food log entry.
    This will update consumption patterns and scores.
    """
    item = get_object_or_404(InventoryItem, pk=pk, user=request.user)
    
    if request.method == 'POST':
        # Mark item as consumed
        item.status = 'consumed'
        item.save()
        
        # Create a FoodLog entry to track consumption
        # This ensures the consumption is reflected in analytics and scores
        from logs.models import FoodLog
        from django.utils import timezone
        
        # Check if a log entry already exists for this item today
        today = timezone.now().date()
        existing_log = FoodLog.objects.filter(
            user=request.user,
            item_name=item.item_name,
            category=item.category,
            date_consumed=today
        ).first()
        
        if existing_log:
            # Update existing log with the consumed quantity
            existing_log.quantity += item.quantity
            existing_log.save()
        else:
            # Create new log entry
            FoodLog.objects.create(
                user=request.user,
                item_name=item.item_name,
                quantity=item.quantity,
                unit=item.unit,
                category=item.category,
                date_consumed=today,
                notes=f'Marked as consumed from inventory (ID: {item.id})'
            )
        
        messages.success(
            request, 
            f'"{item.item_name}" marked as consumed! Consumption logged and scores will be updated.'
        )
        return redirect('inventory:list')
    
    return render(request, 'inventory/mark_consumed.html', {'item': item})


# Food Items Reference Database Views
@login_required
def food_items_list(request):
    """
    Display list of food items from the reference database.
    """
    food_items = FoodItem.objects.all()
    filter_form = FoodItemFilterForm(request.GET)
    
    # Apply filters
    if filter_form.is_valid():
        category = filter_form.cleaned_data.get('category')
        search = filter_form.cleaned_data.get('search')
        
        if category:
            food_items = food_items.filter(category=category)
        if search:
            food_items = food_items.filter(
                Q(name__icontains=search) |
                Q(description__icontains=search)
            )
    
    # Statistics
    total_items = food_items.count()
    
    # Category breakdown
    category_stats = food_items.values('category').annotate(
        count=Count('id')
    ).order_by('-count')
    
    # Group by category for better display
    items_by_category = {}
    for item in food_items:
        category_name = item.get_category_display()
        if category_name not in items_by_category:
            items_by_category[category_name] = []
        items_by_category[category_name].append(item)
    
    context = {
        'food_items': food_items,
        'filter_form': filter_form,
        'total_items': total_items,
        'category_stats': category_stats,
        'items_by_category': items_by_category,
    }
    
    return render(request, 'inventory/food_items_list.html', context)


@login_required
def food_item_detail(request, pk):
    """
    View details of a food item from the reference database.
    """
    food_item = get_object_or_404(FoodItem, pk=pk)
    
    # Get similar items in the same category
    similar_items = FoodItem.objects.filter(
        category=food_item.category
    ).exclude(pk=food_item.pk)[:5]
    
    context = {
        'food_item': food_item,
        'similar_items': similar_items,
    }
    
    return render(request, 'inventory/food_item_detail.html', context)
