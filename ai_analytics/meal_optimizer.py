"""
AI Meal Optimization Engine
Optimizes weekly meal plans based on budget, inventory, and nutrition requirements.
"""

from decimal import Decimal
from datetime import datetime, timedelta
from django.utils import timezone
from inventory.models import InventoryItem, FoodItem
from logs.models import FoodLog


class MealOptimizer:
    """
    Optimizes meal plans to fit budget, use inventory, and meet nutrition requirements.
    """
    
    # Simplified nutrition values per serving (in grams or standard units)
    NUTRITION_PER_SERVING = {
        'vegetable': {'calories': 25, 'protein': 2, 'fiber': 3, 'vitamins': 8},
        'fruit': {'calories': 60, 'protein': 1, 'fiber': 2, 'vitamins': 9},
        'dairy': {'calories': 150, 'protein': 8, 'calcium': 10, 'vitamins': 5},
        'meat': {'calories': 200, 'protein': 25, 'iron': 8, 'vitamins': 6},
        'grain': {'calories': 100, 'protein': 4, 'fiber': 2, 'vitamins': 3},
    }
    
    # Daily nutrition targets (simplified)
    DAILY_TARGETS = {
        'calories': 2000,
        'protein': 50,  # grams
        'fiber': 25,   # grams
        'vitamins': 70,  # arbitrary units
    }
    
    def __init__(self, user):
        self.user = user
        self.profile = getattr(user, 'profile', None)
        self.inventory_items = InventoryItem.objects.filter(
            user=user,
            status__in=['fresh', 'expiring_soon']
        )
        self.food_items_db = FoodItem.objects.all()
    
    def optimize_weekly_meal_plan(self, budget_limit=None):
        """
        Generate an optimized weekly meal plan.
        Returns meal plan with shopping list and estimated costs.
        """
        if budget_limit is None:
            # Get budget from profile
            budget_map = {'low': 50, 'medium': 75, 'high': 100}
            budget_range = self.profile.budget_range if self.profile else 'medium'
            budget_limit = budget_map.get(budget_range, 75)
        
        # Get available inventory
        available_items = list(self.inventory_items)
        
        # Calculate what we need for the week
        weekly_targets = {
            k: v * 7 for k, v in self.DAILY_TARGETS.items()
        }
        
        # Build meal plan prioritizing inventory items
        meal_plan = {
            'days': [],
            'shopping_list': [],
            'total_cost': Decimal('0.00'),
            'nutrition_summary': {},
            'waste_reduction': 0
        }
        
        days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        used_inventory = []
        remaining_targets = weekly_targets.copy()
        
        for day in days:
            day_plan = {
                'day': day,
                'meals': {
                    'breakfast': [],
                    'lunch': [],
                    'dinner': []
                },
                'nutrition': {'calories': 0, 'protein': 0, 'fiber': 0, 'vitamins': 0}
            }
            
            # Prioritize using inventory items (especially expiring ones)
            for item in available_items:
                if item in used_inventory:
                    continue
                
                if item.status == 'expiring_soon':
                    # Use expiring items first
                    day_plan['meals']['lunch'].append({
                        'item': item.item_name,
                        'quantity': float(item.quantity),
                        'unit': item.unit,
                        'source': 'inventory',
                        'expiring': True
                    })
                    used_inventory.append(item)
                    meal_plan['waste_reduction'] += 1
                    break
            
            # Fill remaining nutrition needs
            for meal_type in ['breakfast', 'lunch', 'dinner']:
                if len(day_plan['meals'][meal_type]) == 0:
                    # Suggest items from food database
                    suggested = self._suggest_meal_item(meal_type, remaining_targets)
                    if suggested:
                        day_plan['meals'][meal_type].append(suggested)
                        # Update remaining targets
                        for nutrient, value in suggested.get('nutrition', {}).items():
                            if nutrient in remaining_targets:
                                remaining_targets[nutrient] = max(0, remaining_targets[nutrient] - value)
            
            meal_plan['days'].append(day_plan)
        
        # Generate shopping list for items not in inventory
        meal_plan['shopping_list'] = self._generate_shopping_list(meal_plan, available_items)
        meal_plan['total_cost'] = self._calculate_total_cost(meal_plan['shopping_list'])
        meal_plan['nutrition_summary'] = self._calculate_nutrition_summary(meal_plan)
        
        return meal_plan
    
    def _suggest_meal_item(self, meal_type, remaining_targets):
        """Suggest an item for a meal based on nutrition needs."""
        # Meal-specific preferences
        meal_categories = {
            'breakfast': ['grain', 'fruit', 'dairy'],
            'lunch': ['vegetable', 'meat', 'grain'],
            'dinner': ['meat', 'vegetable', 'grain']
        }
        
        preferred_categories = meal_categories.get(meal_type, ['other'])
        
        # Find items that help meet remaining targets
        for category in preferred_categories:
            food_item = self.food_items_db.filter(category=category).first()
            if food_item:
                nutrition = self.NUTRITION_PER_SERVING.get(category, {})
                return {
                    'item': food_item.name,
                    'quantity': 1,
                    'unit': 'serving',
                    'source': 'food_database',
                    'category': category,
                    'cost': float(food_item.sample_cost_per_unit or 0),
                    'nutrition': nutrition
                }
        
        return None
    
    def _generate_shopping_list(self, meal_plan, available_items):
        """Generate shopping list for items needed but not in inventory."""
        shopping_list = []
        needed_items = {}
        
        # Extract needed items from meal plan
        for day in meal_plan['days']:
            for meal_type, meals in day['meals'].items():
                for meal in meals:
                    if meal.get('source') == 'food_database':
                        item_name = meal['item']
                        if item_name not in needed_items:
                            needed_items[item_name] = {
                                'quantity': 0,
                                'unit': meal.get('unit', 'serving'),
                                'category': meal.get('category', 'other'),
                                'cost': meal.get('cost', 0)
                            }
                        needed_items[item_name]['quantity'] += meal.get('quantity', 1)
        
        # Convert to list
        for item_name, details in needed_items.items():
            food_item = self.food_items_db.filter(name=item_name).first()
            if food_item:
                shopping_list.append({
                    'name': item_name,
                    'quantity': details['quantity'],
                    'unit': details['unit'],
                    'estimated_cost': Decimal(str(details['cost'] * details['quantity'])),
                    'category': details['category']
                })
        
        return shopping_list
    
    def _calculate_total_cost(self, shopping_list):
        """Calculate total estimated cost."""
        total = Decimal('0.00')
        for item in shopping_list:
            total += item.get('estimated_cost', Decimal('0.00'))
        return total
    
    def _calculate_nutrition_summary(self, meal_plan):
        """Calculate total nutrition for the week."""
        summary = {'calories': 0, 'protein': 0, 'fiber': 0, 'vitamins': 0}
        
        for day in meal_plan['days']:
            for nutrient in summary.keys():
                summary[nutrient] += day['nutrition'].get(nutrient, 0)
        
        return summary

