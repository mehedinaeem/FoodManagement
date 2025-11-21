from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count, Q
from django.utils import timezone
from datetime import timedelta
from .models import InventoryItem
from .forms import InventoryItemForm, InventoryFilterForm


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
    
    context = {
        'items': items,
        'filter_form': filter_form,
        'total_items': total_items,
        'fresh_items': fresh_items,
        'expiring_soon': expiring_soon,
        'expired_items': expired_items,
        'category_stats': category_stats,
        'expiring_items': expiring_items,
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
    Mark an inventory item as consumed.
    """
    item = get_object_or_404(InventoryItem, pk=pk, user=request.user)
    
    if request.method == 'POST':
        item.status = 'consumed'
        item.save()
        messages.success(request, f'"{item.item_name}" marked as consumed!')
        return redirect('inventory:list')
    
    return render(request, 'inventory/mark_consumed.html', {'item': item})
