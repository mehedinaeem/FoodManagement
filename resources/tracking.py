"""
Basic tracking logic for analyzing user consumption and inventory,
and recommending relevant resources based on simple rule-based matching.
"""

from collections import Counter
from django.utils import timezone
from datetime import timedelta
from logs.models import FoodLog
from inventory.models import InventoryItem
from resources.models import Resource


class TrackingAnalyzer:
    """
    Analyzes user's food logs and inventory to provide insights
    and resource recommendations.
    """
    
    # Mapping food categories to relevant resource categories
    CATEGORY_MAPPING = {
        'dairy': ['storage_tips', 'waste_reduction', 'preservation'],
        'meat': ['storage_tips', 'waste_reduction', 'preservation'],
        'vegetable': ['storage_tips', 'waste_reduction', 'preservation'],
        'fruit': ['storage_tips', 'waste_reduction', 'preservation'],
        'grain': ['storage_tips', 'preservation'],
        'beverage': ['storage_tips', 'waste_reduction'],
        'snack': ['waste_reduction', 'budget_tips'],
        'other': ['waste_reduction', 'storage_tips'],
    }
    
    # General recommendations based on patterns
    PATTERN_RECOMMENDATIONS = {
        'high_waste_risk': ['waste_reduction', 'meal_planning'],
        'expiring_items': ['storage_tips', 'preservation', 'waste_reduction'],
        'many_categories': ['meal_planning', 'budget_tips'],
        'recent_activity': ['nutrition', 'sustainability'],
    }
    
    def __init__(self, user):
        self.user = user
        self.food_logs = FoodLog.objects.filter(user=user)
        self.inventory_items = InventoryItem.objects.filter(user=user)
    
    def get_summary(self):
        """
        Get basic summary statistics.
        """
        total_logs = self.food_logs.count()
        total_inventory = self.inventory_items.count()
        
        # Recent activity (last 7 days)
        week_ago = timezone.now().date() - timedelta(days=7)
        recent_logs = self.food_logs.filter(date_consumed__gte=week_ago).count()
        
        # Inventory status
        fresh_items = self.inventory_items.filter(status='fresh').count()
        expiring_soon = self.inventory_items.filter(status='expiring_soon').count()
        expired_items = self.inventory_items.filter(status='expired').count()
        
        # Category breakdown from logs
        log_categories = Counter(
            self.food_logs.values_list('category', flat=True)
        )
        top_logged_categories = dict(log_categories.most_common(5))
        
        # Category breakdown from inventory
        inventory_categories = Counter(
            self.inventory_items.values_list('category', flat=True)
        )
        top_inventory_categories = dict(inventory_categories.most_common(5))
        
        return {
            'total_logs': total_logs,
            'total_inventory': total_inventory,
            'recent_logs': recent_logs,
            'fresh_items': fresh_items,
            'expiring_soon': expiring_soon,
            'expired_items': expired_items,
            'top_logged_categories': top_logged_categories,
            'top_inventory_categories': top_inventory_categories,
        }
    
    def get_recommendations(self, limit=5):
        """
        Get resource recommendations based on user's consumption and inventory patterns.
        Returns list of tuples: (resource, reason, explanation)
        """
        recommendations = []
        reasons = {}
        
        # Analyze food log categories
        log_categories = Counter(
            self.food_logs.values_list('category', flat=True)
        )
        
        # Analyze inventory categories
        inventory_categories = Counter(
            self.inventory_items.values_list('category', flat=True)
        )
        
        # Combine categories (weighted: inventory items are more important)
        all_categories = log_categories.copy()
        for category, count in inventory_categories.items():
            all_categories[category] = all_categories.get(category, 0) + (count * 2)
        
        # Get top categories
        top_categories = [cat for cat, _ in all_categories.most_common(3)]
        
        # Find resources based on category mapping
        resource_categories_to_search = set()
        
        for food_category in top_categories:
            if food_category in self.CATEGORY_MAPPING:
                resource_categories_to_search.update(
                    self.CATEGORY_MAPPING[food_category]
                )
                # Store reason for recommendation
                for res_cat in self.CATEGORY_MAPPING[food_category]:
                    if res_cat not in reasons:
                        reasons[res_cat] = []
                    reasons[res_cat].append(
                        f"Based on your {food_category} consumption/inventory"
                    )
        
        # Pattern-based recommendations
        if self.inventory_items.filter(status='expiring_soon').exists():
            resource_categories_to_search.update(
                self.PATTERN_RECOMMENDATIONS['expiring_items']
            )
            for res_cat in self.PATTERN_RECOMMENDATIONS['expiring_items']:
                if res_cat not in reasons:
                    reasons[res_cat] = []
                reasons[res_cat].append("You have items expiring soon")
        
        if self.inventory_items.filter(status='expired').exists():
            resource_categories_to_search.add('waste_reduction')
            if 'waste_reduction' not in reasons:
                reasons['waste_reduction'] = []
            reasons['waste_reduction'].append("You have expired items")
        
        if self.food_logs.count() > 10 and len(all_categories) > 5:
            resource_categories_to_search.update(
                self.PATTERN_RECOMMENDATIONS['many_categories']
            )
            for res_cat in self.PATTERN_RECOMMENDATIONS['many_categories']:
                if res_cat not in reasons:
                    reasons[res_cat] = []
                reasons[res_cat].append("You track multiple food categories")
        
        # Get resources
        if resource_categories_to_search:
            resources = Resource.objects.filter(
                category__in=resource_categories_to_search
            ).distinct()
            
            # Prioritize featured resources
            featured = resources.filter(featured=True)
            non_featured = resources.exclude(featured=True)
            
            # Add featured first
            for resource in featured[:limit]:
                category = resource.category
                explanation = self._generate_explanation(category, reasons.get(category, []))
                recommendations.append((resource, category, explanation))
            
            # Add non-featured if we need more
            remaining = limit - len(recommendations)
            if remaining > 0:
                for resource in non_featured[:remaining]:
                    category = resource.category
                    explanation = self._generate_explanation(category, reasons.get(category, []))
                    recommendations.append((resource, category, explanation))
        
        # If no specific recommendations, suggest general ones
        if not recommendations:
            general_resources = Resource.objects.filter(
                category__in=['waste_reduction', 'storage_tips', 'meal_planning']
            ).filter(featured=True)[:limit]
            
            for resource in general_resources:
                explanation = "General recommendation for sustainable food practices"
                recommendations.append((resource, resource.category, explanation))
        
        return recommendations[:limit]
    
    def _generate_explanation(self, resource_category, reasons):
        """
        Generate a human-readable explanation for why a resource is recommended.
        """
        category_dict = dict(Resource.CATEGORY_CHOICES)
        category_display = category_dict.get(resource_category, resource_category.replace('_', ' ').title())
        
        if not reasons:
            return f"Related to: {category_display}"
        
        # Format reasons nicely
        if len(reasons) == 1:
            return f"Recommended because: {reasons[0]}"
        else:
            main_reason = reasons[0]
            return f"Recommended because: {main_reason} (and {len(reasons)-1} other reason{'s' if len(reasons) > 2 else ''})"
    
    def get_insights(self):
        """
        Get insights and patterns from user data.
        """
        insights = []
        
        # Check for expiring items
        expiring_count = self.inventory_items.filter(status='expiring_soon').count()
        if expiring_count > 0:
            insights.append({
                'type': 'warning',
                'message': f'You have {expiring_count} item(s) expiring soon. Consider using them or preserving them.',
                'action': 'View expiring items',
                'action_url': '/inventory/?status=expiring_soon'
            })
        
        # Check for expired items
        expired_count = self.inventory_items.filter(status='expired').count()
        if expired_count > 0:
            insights.append({
                'type': 'danger',
                'message': f'You have {expired_count} expired item(s). Review your inventory to reduce waste.',
                'action': 'View expired items',
                'action_url': '/inventory/?status=expired'
            })
        
        # Check for recent activity
        week_ago = timezone.now().date() - timedelta(days=7)
        recent_logs = self.food_logs.filter(date_consumed__gte=week_ago).count()
        if recent_logs == 0 and self.food_logs.count() > 0:
            insights.append({
                'type': 'info',
                'message': 'You haven\'t logged any food consumption in the past week. Keep tracking to get better insights!',
                'action': 'Log food',
                'action_url': '/logs/create/'
            })
        
        # Check for inventory size
        if self.inventory_items.count() > 20:
            insights.append({
                'type': 'info',
                'message': 'You have a large inventory. Consider meal planning to use items efficiently.',
                'action': 'View resources',
                'action_url': '/resources/?category=meal_planning'
            })
        
        return insights

