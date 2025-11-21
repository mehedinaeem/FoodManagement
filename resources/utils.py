"""
Utility functions for resource recommendations based on user activity.
"""
from django.db.models import Count, Q
from logs.models import FoodLog
from inventory.models import InventoryItem
from .models import Resource


def get_user_categories(user):
    """
    Get categories from user's food logs and inventory.
    Returns a dictionary with category counts.
    """
    # Get categories from food logs
    log_categories = FoodLog.objects.filter(user=user).values('category').annotate(
        count=Count('id')
    )
    
    # Get categories from inventory
    inventory_categories = InventoryItem.objects.filter(user=user).values('category').annotate(
        count=Count('id')
    )
    
    # Combine categories
    category_counts = {}
    
    for item in log_categories:
        category = item['category']
        count = item['count']
        category_counts[category] = category_counts.get(category, 0) + count
    
    for item in inventory_categories:
        category = item['category']
        count = item['count']
        category_counts[category] = category_counts.get(category, 0) + count
    
    return category_counts


def get_category_resource_mapping():
    """
    Map food categories to resource categories for recommendations.
    Returns a dictionary mapping food categories to resource categories.
    """
    return {
        'dairy': ['storage_tips', 'waste_reduction', 'preservation'],
        'vegetable': ['storage_tips', 'waste_reduction', 'preservation', 'cooking_tips'],
        'fruit': ['storage_tips', 'waste_reduction', 'preservation'],
        'meat': ['storage_tips', 'waste_reduction', 'preservation'],
        'grain': ['storage_tips', 'preservation', 'budget_tips'],
        'beverage': ['storage_tips', 'waste_reduction'],
        'snack': ['storage_tips', 'budget_tips'],
        'frozen': ['storage_tips', 'preservation'],
        'canned': ['storage_tips', 'budget_tips'],
    }


def recommend_resources(user, limit=5):
    """
    Recommend resources based on user's food logs and inventory.
    Returns a list of recommended resources with reasons.
    """
    # Get user's categories
    user_categories = get_user_categories(user)
    
    if not user_categories:
        # If no categories, return general recommendations
        return Resource.objects.filter(
            featured=True
        )[:limit]
    
    # Get category mapping
    category_mapping = get_category_resource_mapping()
    
    # Find relevant resource categories
    relevant_resource_categories = set()
    category_reasons = {}  # Track why each category is relevant
    
    for food_category, count in user_categories.items():
        if food_category in category_mapping:
            resource_categories = category_mapping[food_category]
            for resource_category in resource_categories:
                relevant_resource_categories.add(resource_category)
                if resource_category not in category_reasons:
                    category_reasons[resource_category] = []
                category_reasons[resource_category].append({
                    'food_category': food_category,
                    'count': count
                })
    
    # Get resources matching relevant categories
    recommended_resources = []
    
    # First, try to get resources from relevant categories
    if relevant_resource_categories:
        resources = Resource.objects.filter(
            category__in=relevant_resource_categories
        ).distinct()[:limit * 2]  # Get more to have options
        
        for resource in resources:
            reason = category_reasons.get(resource.category, [])
            if reason:
                # Build explanation
                explanations = []
                for r in reason:
                    food_cat_display = dict(FoodLog.CATEGORY_CHOICES).get(
                        r['food_category'], r['food_category']
                    )
                    explanations.append(f"{food_cat_display} (used {r['count']} time{'s' if r['count'] > 1 else ''})")
                
                recommended_resources.append({
                    'resource': resource,
                    'reason': f"Related to: {', '.join(explanations)}",
                    'category': resource.category
                })
    
    # If we don't have enough recommendations, add featured resources
    if len(recommended_resources) < limit:
        featured = Resource.objects.filter(featured=True).exclude(
            pk__in=[r['resource'].pk for r in recommended_resources]
        )[:limit - len(recommended_resources)]
        
        for resource in featured:
            recommended_resources.append({
                'resource': resource,
                'reason': 'Featured resource',
                'category': resource.category
            })
    
    # If still not enough, add general resources
    if len(recommended_resources) < limit:
        general = Resource.objects.exclude(
            pk__in=[r['resource'].pk for r in recommended_resources]
        )[:limit - len(recommended_resources)]
        
        for resource in general:
            recommended_resources.append({
                'resource': resource,
                'reason': 'General recommendation',
                'category': resource.category
            })
    
    return recommended_resources[:limit]


def get_tracking_summary(user):
    """
    Get a summary of user's tracking data.
    Returns a dictionary with various statistics.
    """
    # Food logs statistics
    total_logs = FoodLog.objects.filter(user=user).count()
    recent_logs = FoodLog.objects.filter(user=user).order_by('-date_consumed')[:5]
    
    # Inventory statistics
    total_inventory = InventoryItem.objects.filter(user=user).count()
    fresh_inventory = InventoryItem.objects.filter(user=user, status='fresh').count()
    expiring_soon = InventoryItem.objects.filter(user=user, status='expiring_soon').count()
    
    # Category usage
    category_counts = get_user_categories(user)
    top_categories = sorted(
        category_counts.items(), 
        key=lambda x: x[1], 
        reverse=True
    )[:5]
    
    # Recent activity
    recent_activity = []
    
    # Add recent logs
    for log in recent_logs:
        recent_activity.append({
            'type': 'log',
            'item': log.item_name,
            'date': log.date_consumed,
            'category': log.category,
            'description': f"Consumed {log.quantity} {log.unit}"
        })
    
    # Add recent inventory items
    recent_inventory = InventoryItem.objects.filter(user=user).order_by('-created_at')[:3]
    for item in recent_inventory:
        recent_activity.append({
            'type': 'inventory',
            'item': item.item_name,
            'date': item.created_at.date(),
            'category': item.category,
            'description': f"Added {item.quantity} {log.unit}" if 'log' in locals() else f"Added {item.quantity} {item.unit}"
        })
    
    # Sort by date
    recent_activity.sort(key=lambda x: x['date'], reverse=True)
    
    return {
        'total_logs': total_logs,
        'total_inventory': total_inventory,
        'fresh_inventory': fresh_inventory,
        'expiring_soon': expiring_soon,
        'top_categories': top_categories,
        'category_counts': category_counts,
        'recent_activity': recent_activity[:10],
    }

