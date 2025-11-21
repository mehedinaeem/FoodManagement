"""
AI Meal Optimization Engine
Optimizes weekly meal plans based on budget, inventory, and nutrition requirements.
Enhanced with LLM support and local cost data.
"""

import json
import os
from decimal import Decimal
from datetime import datetime, timedelta
from collections import defaultdict
from django.utils import timezone
from django.conf import settings
from inventory.models import InventoryItem, FoodItem
from logs.models import FoodLog


class MealOptimizer:
    """
    Advanced meal optimizer with budget constraints, inventory prioritization,
    nutrition requirements, and cost-based alternatives.
    """
    
    # Enhanced nutrition values per serving
    NUTRITION_PER_SERVING = {
        'vegetable': {'calories': 25, 'protein': 2, 'fiber': 3, 'vitamins': 8, 'iron': 0.5, 'calcium': 2},
        'fruit': {'calories': 60, 'protein': 1, 'fiber': 2, 'vitamins': 9, 'iron': 0.3, 'calcium': 1},
        'dairy': {'calories': 150, 'protein': 8, 'calcium': 10, 'vitamins': 5, 'iron': 0.1, 'fiber': 0},
        'meat': {'calories': 200, 'protein': 25, 'iron': 8, 'vitamins': 6, 'calcium': 0.5, 'fiber': 0},
        'grain': {'calories': 100, 'protein': 4, 'fiber': 2, 'vitamins': 3, 'iron': 1, 'calcium': 0.5},
        'beverage': {'calories': 50, 'protein': 0, 'fiber': 0, 'vitamins': 2, 'iron': 0, 'calcium': 1},
        'snack': {'calories': 120, 'protein': 2, 'fiber': 1, 'vitamins': 1, 'iron': 0.2, 'calcium': 0.5},
        'other': {'calories': 80, 'protein': 2, 'fiber': 1, 'vitamins': 2, 'iron': 0.3, 'calcium': 0.5},
    }
    
    # Daily nutrition targets (enhanced)
    DAILY_TARGETS = {
        'calories': 2000,
        'protein': 50,   # grams
        'fiber': 25,     # grams
        'vitamins': 70,  # arbitrary units
        'iron': 18,      # mg
        'calcium': 1000, # mg
    }
    
    # Local cost data (dummy dataset - in production, use real API)
    LOCAL_COST_DATA = {
        'vegetable': {'base': 2.50, 'min': 1.50, 'max': 4.00, 'seasonal_factor': 0.8},
        'fruit': {'base': 3.00, 'min': 2.00, 'max': 5.00, 'seasonal_factor': 0.7},
        'dairy': {'base': 4.00, 'min': 3.00, 'max': 6.00, 'seasonal_factor': 1.0},
        'meat': {'base': 8.00, 'min': 6.00, 'max': 12.00, 'seasonal_factor': 1.0},
        'grain': {'base': 2.00, 'min': 1.50, 'max': 3.50, 'seasonal_factor': 1.0},
        'beverage': {'base': 2.50, 'min': 1.50, 'max': 4.00, 'seasonal_factor': 1.0},
        'snack': {'base': 3.50, 'min': 2.00, 'max': 5.00, 'seasonal_factor': 1.0},
        'other': {'base': 3.00, 'min': 2.00, 'max': 5.00, 'seasonal_factor': 1.0},
    }
    
    # Alternative food mappings (cheaper alternatives)
    ALTERNATIVE_FOODS = {
        'meat': ['grain', 'dairy'],  # Can substitute with protein-rich alternatives
        'dairy': ['grain', 'vegetable'],
        'fruit': ['vegetable'],  # Vegetables can provide similar nutrients
        'snack': ['fruit', 'grain'],
    }
    
    def __init__(self, user):
        self.user = user
        self.profile = getattr(user, 'profile', None)
        self.inventory_items = InventoryItem.objects.filter(
            user=user,
            status__in=['fresh', 'expiring_soon']
        ).order_by('expiration_date', 'status')
        self.food_items_db = FoodItem.objects.all()
        self.household_size = self.profile.household_size if self.profile else 1
    
    def optimize_weekly_meal_plan(self, budget_limit=None, use_llm=False):
        """
        Generate an optimized weekly meal plan.
        
        Args:
            budget_limit: Weekly budget in USD
            use_llm: Whether to use LLM for optimization (falls back to rule-based)
        
        Returns:
            Dictionary with meal plan, shopping list, costs, and nutrition summary
        """
        if budget_limit is None:
            budget_map = {'low': 50, 'medium': 75, 'high': 100}
            budget_range = self.profile.budget_range if self.profile else 'medium'
            budget_limit = budget_map.get(budget_range, 75)
        
        # Adjust targets for household size
        weekly_targets = {
            k: v * 7 * self.household_size for k, v in self.DAILY_TARGETS.items()
        }
        
        # Get available inventory (prioritize expiring items)
        available_items = list(self.inventory_items)
        expiring_items = [item for item in available_items if item.status == 'expiring_soon']
        fresh_items = [item for item in available_items if item.status == 'fresh']
        
        # Use LLM if requested and available
        if use_llm and self._has_openai_key():
            return self._optimize_with_llm(budget_limit, weekly_targets, available_items)
        else:
            return self._optimize_rule_based(budget_limit, weekly_targets, available_items, expiring_items, fresh_items)
    
    def _optimize_rule_based(self, budget_limit, weekly_targets, available_items, expiring_items, fresh_items):
        """Rule-based optimization algorithm."""
        meal_plan = {
            'days': [],
            'shopping_list': [],
            'total_cost': Decimal('0.00'),
            'nutrition_summary': {},
            'waste_reduction': 0,
            'budget_used': Decimal('0.00'),
            'budget_limit': Decimal(str(budget_limit)),
            'alternatives_suggested': []
        }
        
        days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        used_inventory = set()
        remaining_targets = weekly_targets.copy()
        remaining_budget = Decimal(str(budget_limit))
        
        # Track nutrition and costs
        total_nutrition = defaultdict(float)
        inventory_used = []
        
        for day_idx, day in enumerate(days):
            day_plan = {
                'day': day,
                'meals': {
                    'breakfast': [],
                    'lunch': [],
                    'dinner': []
                },
                'nutrition': defaultdict(float),
                'cost': Decimal('0.00')
            }
            
            # Meal types with their preferred categories
            meal_configs = [
                ('breakfast', ['grain', 'fruit', 'dairy']),
                ('lunch', ['vegetable', 'meat', 'grain']),
                ('dinner', ['meat', 'vegetable', 'grain'])
            ]
            
            for meal_type, preferred_categories in meal_configs:
                meal_items = []
                
                # First, try to use expiring inventory items
                for item in expiring_items:
                    if item.id not in used_inventory and item.category in preferred_categories:
                        meal_items.append(self._create_meal_item_from_inventory(item, expiring=True))
                        used_inventory.add(item.id)
                        inventory_used.append(item)
                        meal_plan['waste_reduction'] += 1
                        break
                
                # Then, try fresh inventory items
                if not meal_items:
                    for item in fresh_items:
                        if item.id not in used_inventory and item.category in preferred_categories:
                            meal_items.append(self._create_meal_item_from_inventory(item, expiring=False))
                            used_inventory.add(item.id)
                            inventory_used.append(item)
                            break
                
                # If no inventory, suggest from food database with cost optimization
                if not meal_items:
                    suggested = self._suggest_meal_item_optimized(
                        meal_type, preferred_categories, remaining_targets, remaining_budget
                    )
                    if suggested:
                        meal_items.append(suggested)
                        remaining_budget -= Decimal(str(suggested.get('cost', 0)))
                
                # Add items to meal
                for item in meal_items:
                    day_plan['meals'][meal_type].append(item)
                    
                    # Update nutrition
                    nutrition = item.get('nutrition', {})
                    for nutrient, value in nutrition.items():
                        day_plan['nutrition'][nutrient] += value
                        total_nutrition[nutrient] += value
                        if nutrient in remaining_targets:
                            remaining_targets[nutrient] = max(0, remaining_targets[nutrient] - value)
                    
                    # Update cost
                    day_plan['cost'] += Decimal(str(item.get('cost', 0)))
            
            meal_plan['days'].append(day_plan)
        
        # Generate shopping list
        meal_plan['shopping_list'] = self._generate_shopping_list_optimized(
            meal_plan, available_items, budget_limit
        )
        meal_plan['total_cost'] = self._calculate_total_cost(meal_plan['shopping_list'])
        meal_plan['budget_used'] = meal_plan['total_cost']
        
        # Calculate nutrition summary
        meal_plan['nutrition_summary'] = dict(total_nutrition)
        
        # Check if we need alternatives due to budget
        if meal_plan['total_cost'] > Decimal(str(budget_limit)):
            meal_plan['alternatives_suggested'] = self._suggest_cost_alternatives(
                meal_plan['shopping_list'], budget_limit
            )
        
        return meal_plan
    
    def _create_meal_item_from_inventory(self, inventory_item, expiring=False):
        """Create meal item from inventory."""
        category = inventory_item.category
        nutrition = self.NUTRITION_PER_SERVING.get(category, {})
        
        # Scale nutrition by quantity
        scaled_nutrition = {
            k: v * float(inventory_item.quantity) 
            for k, v in nutrition.items()
        }
        
        return {
            'item': inventory_item.item_name,
            'quantity': float(inventory_item.quantity),
            'unit': inventory_item.unit,
            'source': 'inventory',
            'expiring': expiring,
            'category': category,
            'cost': Decimal('0.00'),  # Already owned
            'nutrition': scaled_nutrition,
            'inventory_id': inventory_item.id
        }
    
    def _suggest_meal_item_optimized(self, meal_type, preferred_categories, remaining_targets, remaining_budget):
        """Suggest meal item optimized for nutrition and cost."""
        best_item = None
        best_score = -1
        
        for category in preferred_categories:
            # Get food items in this category
            food_items = self.food_items_db.filter(category=category)
            
            for food_item in food_items:
                # Calculate cost
                cost = self._get_local_cost(category, food_item)
                
                # Skip if too expensive
                if cost > remaining_budget:
                    continue
                
                # Calculate nutrition score
                nutrition = self.NUTRITION_PER_SERVING.get(category, {})
                nutrition_score = sum(
                    min(1.0, nutrition.get(nutrient, 0) / max(1, remaining_targets.get(nutrient, 1)))
                    for nutrient in remaining_targets.keys()
                    if remaining_targets.get(nutrient, 0) > 0
                )
                
                # Calculate value score (nutrition per dollar)
                if cost > 0:
                    value_score = nutrition_score / float(cost)
                else:
                    value_score = nutrition_score
                
                if value_score > best_score:
                    best_score = value_score
                    best_item = {
                        'item': food_item.name,
                        'quantity': 1,
                        'unit': food_item.unit or 'serving',
                        'source': 'food_database',
                        'category': category,
                        'cost': cost,
                        'nutrition': nutrition,
                        'food_item_id': food_item.id
                    }
        
        return best_item
    
    def _get_local_cost(self, category, food_item):
        """Get local cost for a food item (using dummy data)."""
        cost_data = self.LOCAL_COST_DATA.get(category, {'base': 3.00})
        
        # Use food item's cost if available, otherwise use local cost data
        if food_item.sample_cost_per_unit:
            base_cost = float(food_item.sample_cost_per_unit)
        else:
            base_cost = cost_data['base']
        
        # Apply seasonal/local variations (dummy)
        seasonal_factor = cost_data.get('seasonal_factor', 1.0)
        adjusted_cost = base_cost * seasonal_factor
        
        return Decimal(str(adjusted_cost))
    
    def _generate_shopping_list_optimized(self, meal_plan, available_items, budget_limit):
        """Generate optimized shopping list with cost alternatives."""
        shopping_list = []
        needed_items = defaultdict(lambda: {'quantity': 0, 'unit': 'serving', 'category': 'other', 'cost': 0, 'items': []})
        
        # Extract needed items from meal plan
        for day in meal_plan['days']:
            for meal_type, meals in day['meals'].items():
                for meal in meals:
                    if meal.get('source') == 'food_database':
                        item_name = meal['item']
                        category = meal.get('category', 'other')
                        cost = float(meal.get('cost', 0))
                        
                        needed_items[item_name]['quantity'] += meal.get('quantity', 1)
                        needed_items[item_name]['unit'] = meal.get('unit', 'serving')
                        needed_items[item_name]['category'] = category
                        needed_items[item_name]['cost'] = cost
                        needed_items[item_name]['items'].append(meal)
        
        # Convert to list with alternatives
        total_cost = Decimal('0.00')
        for item_name, details in needed_items.items():
            estimated_cost = Decimal(str(details['cost'] * details['quantity']))
            total_cost += estimated_cost
            
            # Check if we need cheaper alternatives
            alternatives = []
            if total_cost > Decimal(str(budget_limit * 0.8)):  # If using >80% of budget
                alternatives = self._find_cheaper_alternatives(
                    details['category'], details['cost']
                )
            
            shopping_list.append({
                'name': item_name,
                'quantity': details['quantity'],
                'unit': details['unit'],
                'estimated_cost': estimated_cost,
                'category': details['category'],
                'alternatives': alternatives
            })
        
        return shopping_list
    
    def _find_cheaper_alternatives(self, category, current_cost):
        """Find cheaper alternatives for a category."""
        alternatives = []
        alt_categories = self.ALTERNATIVE_FOODS.get(category, [])
        
        for alt_category in alt_categories:
            cost_data = self.LOCAL_COST_DATA.get(alt_category, {'base': 3.00})
            alt_cost = cost_data['base'] * cost_data.get('seasonal_factor', 1.0)
            
            if alt_cost < current_cost * 0.8:  # At least 20% cheaper
                food_items = self.food_items_db.filter(category=alt_category)[:2]
                for food_item in food_items:
                    alternatives.append({
                        'name': food_item.name,
                        'category': alt_category,
                        'estimated_savings': current_cost - alt_cost,
                        'cost': alt_cost
                    })
        
        return alternatives[:2]  # Return top 2 alternatives
    
    def _suggest_cost_alternatives(self, shopping_list, budget_limit):
        """Suggest alternatives when budget is exceeded."""
        suggestions = []
        total_cost = sum(item['estimated_cost'] for item in shopping_list)
        
        if total_cost > Decimal(str(budget_limit)):
            over_budget = total_cost - Decimal(str(budget_limit))
            
            # Find most expensive items
            sorted_items = sorted(shopping_list, key=lambda x: x['estimated_cost'], reverse=True)
            
            for item in sorted_items[:3]:  # Top 3 most expensive
                if item.get('alternatives'):
                    suggestions.append({
                        'original': item['name'],
                        'original_cost': item['estimated_cost'],
                        'alternatives': item['alternatives'],
                        'potential_savings': sum(alt['estimated_savings'] for alt in item['alternatives'])
                    })
        
        return suggestions
    
    def _calculate_total_cost(self, shopping_list):
        """Calculate total estimated cost."""
        total = Decimal('0.00')
        for item in shopping_list:
            total += item.get('estimated_cost', Decimal('0.00'))
        return total
    
    def _optimize_with_llm(self, budget_limit, weekly_targets, available_items):
        """Optimize meal plan using LLM (OpenAI)."""
        try:
            import openai
            
            api_key = os.getenv('OPENAI_API_KEY') or getattr(settings, 'OPENAI_API_KEY', None)
            if not api_key:
                return self._optimize_rule_based(
                    budget_limit, weekly_targets, available_items, 
                    [i for i in available_items if i.status == 'expiring_soon'],
                    [i for i in available_items if i.status == 'fresh']
                )
            
            client = openai.OpenAI(api_key=api_key)
            
            # Prepare context
            inventory_summary = [
                f"{item.item_name} ({item.category}, {item.quantity} {item.unit}, expires: {item.expiration_date})"
                for item in available_items[:10]
            ]
            
            prompt = f"""Create an optimized weekly meal plan with the following constraints:
- Budget: ${budget_limit} per week
- Household size: {self.household_size}
- Available inventory: {', '.join(inventory_summary)}
- Daily nutrition targets: {json.dumps(self.DAILY_TARGETS)}
- Prioritize using inventory items, especially expiring ones
- Ensure all nutrition requirements are met
- Suggest cost-effective alternatives if needed

Return a JSON structure with:
- days: array of 7 days (Monday-Sunday)
- Each day should have breakfast, lunch, dinner
- Each meal should specify: item name, quantity, unit, source (inventory/food_database), cost, nutrition values
- shopping_list: items needed to purchase
- total_cost: total estimated cost
- nutrition_summary: weekly totals

Format the response as valid JSON only."""
            
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a meal planning expert. Return only valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=2000
            )
            
            # Parse LLM response
            llm_result = json.loads(response.choices[0].message.content)
            
            # Convert to our format
            meal_plan = {
                'days': llm_result.get('days', []),
                'shopping_list': llm_result.get('shopping_list', []),
                'total_cost': Decimal(str(llm_result.get('total_cost', 0))),
                'nutrition_summary': llm_result.get('nutrition_summary', {}),
                'waste_reduction': len([item for item in available_items if item.status == 'expiring_soon']),
                'budget_used': Decimal(str(llm_result.get('total_cost', 0))),
                'budget_limit': Decimal(str(budget_limit)),
                'alternatives_suggested': llm_result.get('alternatives_suggested', []),
                'optimization_method': 'LLM'
            }
            
            return meal_plan
            
        except Exception as e:
            # Fallback to rule-based
            return self._optimize_rule_based(
                budget_limit, weekly_targets, available_items,
                [i for i in available_items if i.status == 'expiring_soon'],
                [i for i in available_items if i.status == 'fresh']
            )
    
    def _has_openai_key(self):
        """Check if OpenAI API key is available."""
        api_key = os.getenv('OPENAI_API_KEY') or getattr(settings, 'OPENAI_API_KEY', None)
        return api_key is not None
