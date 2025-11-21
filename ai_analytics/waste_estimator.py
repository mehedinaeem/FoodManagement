"""
AI Waste Estimation Model
Estimates wasted food and money from consumption patterns.
"""

from decimal import Decimal
from datetime import datetime, timedelta
from django.utils import timezone
from django.db.models import Sum, Count, Avg
from inventory.models import InventoryItem
from logs.models import FoodLog


class WasteEstimator:
    """
    Estimates food waste based on user patterns and inventory.
    """
    
    # Average waste rates by category (percentage)
    CATEGORY_WASTE_RATES = {
        'vegetable': 0.25,  # 25% waste rate
        'fruit': 0.20,      # 20% waste rate
        'dairy': 0.15,      # 15% waste rate
        'meat': 0.10,       # 10% waste rate
        'grain': 0.05,      # 5% waste rate
        'beverage': 0.08,   # 8% waste rate
        'snack': 0.12,      # 12% waste rate
        'other': 0.15,      # 15% waste rate
    }
    
    # Average cost per unit by category (simplified)
    AVG_COST_PER_UNIT = {
        'vegetable': 2.50,
        'fruit': 3.00,
        'dairy': 4.00,
        'meat': 8.00,
        'grain': 2.00,
        'beverage': 2.50,
        'snack': 3.50,
        'other': 3.00,
    }
    
    # Community average waste (dummy data)
    COMMUNITY_AVERAGE_WASTE = {
        'weekly_grams': 500,  # grams per week
        'weekly_cost': 15.00,  # dollars per week
        'monthly_grams': 2000,
        'monthly_cost': 60.00,
    }
    
    def __init__(self, user):
        self.user = user
        self.inventory_items = InventoryItem.objects.filter(user=user)
        self.food_logs = FoodLog.objects.filter(user=user)
        self.profile = getattr(user, 'profile', None)
    
    def estimate_weekly_waste(self):
        """
        Estimate wasted food for the current week.
        Returns grams and cost estimates.
        """
        # Get items that expired this week
        week_start = timezone.now().date() - timedelta(days=7)
        expired_items = self.inventory_items.filter(
            status='expired',
            expiration_date__gte=week_start
        )
        
        # Calculate waste from expired items
        total_waste_grams = Decimal('0.00')
        total_waste_cost = Decimal('0.00')
        
        for item in expired_items:
            # Convert quantity to grams (simplified conversion)
            grams = self._convert_to_grams(float(item.quantity), item.unit)
            total_waste_grams += Decimal(str(grams))
            
            # Estimate cost
            avg_cost = self.AVG_COST_PER_UNIT.get(item.category, 3.00)
            cost = Decimal(str(avg_cost * float(item.quantity)))
            total_waste_cost += cost
        
        # Estimate waste from consumption patterns
        # Items purchased but not consumed
        week_logs = self.food_logs.filter(
            date_consumed__gte=week_start
        )
        
        # Calculate expected vs actual consumption
        purchased_items = self.inventory_items.filter(
            purchase_date__gte=week_start
        )
        
        pattern_waste = Decimal('0.00')
        pattern_cost = Decimal('0.00')
        
        for item in purchased_items:
            if item.status == 'expired' or item.status == 'expiring_soon':
                waste_rate = self.CATEGORY_WASTE_RATES.get(item.category, 0.15)
                grams = self._convert_to_grams(float(item.quantity), item.unit)
                estimated_waste = Decimal(str(grams * waste_rate))
                pattern_waste += estimated_waste
                
                avg_cost = self.AVG_COST_PER_UNIT.get(item.category, 3.00)
                cost = Decimal(str(avg_cost * float(item.quantity) * waste_rate))
                pattern_cost += cost
        
        return {
            'expired_waste_grams': float(total_waste_grams),
            'expired_waste_cost': float(total_waste_cost),
            'pattern_waste_grams': float(pattern_waste),
            'pattern_waste_cost': float(pattern_cost),
            'total_waste_grams': float(total_waste_grams + pattern_waste),
            'total_waste_cost': float(total_waste_cost + pattern_cost),
            'week_start': week_start,
        }
    
    def estimate_monthly_waste(self):
        """
        Estimate wasted food for the current month.
        """
        month_start = timezone.now().date() - timedelta(days=30)
        
        expired_items = self.inventory_items.filter(
            status='expired',
            expiration_date__gte=month_start
        )
        
        total_waste_grams = Decimal('0.00')
        total_waste_cost = Decimal('0.00')
        
        for item in expired_items:
            grams = self._convert_to_grams(float(item.quantity), item.unit)
            total_waste_grams += Decimal(str(grams))
            
            avg_cost = self.AVG_COST_PER_UNIT.get(item.category, 3.00)
            cost = Decimal(str(avg_cost * float(item.quantity)))
            total_waste_cost += cost
        
        # Project based on weekly average
        weekly_estimate = self.estimate_weekly_waste()
        projected_monthly = {
            'grams': weekly_estimate['total_waste_grams'] * 4,
            'cost': weekly_estimate['total_waste_cost'] * 4,
        }
        
        return {
            'actual_waste_grams': float(total_waste_grams),
            'actual_waste_cost': float(total_waste_cost),
            'projected_waste_grams': projected_monthly['grams'],
            'projected_waste_cost': projected_monthly['cost'],
            'month_start': month_start,
        }
    
    def compare_to_community(self):
        """
        Compare user's waste to community averages.
        """
        weekly = self.estimate_weekly_waste()
        monthly = self.estimate_monthly_waste()
        
        weekly_comparison = {
            'user_grams': weekly['total_waste_grams'],
            'community_grams': self.COMMUNITY_AVERAGE_WASTE['weekly_grams'],
            'user_cost': weekly['total_waste_cost'],
            'community_cost': self.COMMUNITY_AVERAGE_WASTE['weekly_cost'],
            'percentage_difference': ((weekly['total_waste_grams'] - self.COMMUNITY_AVERAGE_WASTE['weekly_grams']) / 
                                     self.COMMUNITY_AVERAGE_WASTE['weekly_grams']) * 100 if self.COMMUNITY_AVERAGE_WASTE['weekly_grams'] > 0 else 0,
        }
        
        monthly_comparison = {
            'user_grams': monthly['projected_waste_grams'],
            'community_grams': self.COMMUNITY_AVERAGE_WASTE['monthly_grams'],
            'user_cost': monthly['projected_waste_cost'],
            'community_cost': self.COMMUNITY_AVERAGE_WASTE['monthly_cost'],
            'percentage_difference': ((monthly['projected_waste_grams'] - self.COMMUNITY_AVERAGE_WASTE['monthly_grams']) / 
                                     self.COMMUNITY_AVERAGE_WASTE['monthly_grams']) * 100 if self.COMMUNITY_AVERAGE_WASTE['monthly_grams'] > 0 else 0,
        }
        
        return {
            'weekly': weekly_comparison,
            'monthly': monthly_comparison,
        }
    
    def _convert_to_grams(self, quantity, unit):
        """Convert various units to grams (simplified)."""
        conversions = {
            'kg': 1000,
            'g': 1,
            'lb': 453.592,
            'oz': 28.3495,
            'l': 1000,  # Assuming density of 1g/ml for liquids
            'ml': 1,
            'cup': 240,  # Approximate for most foods
            'piece': 150,  # Average piece weight
            'serving': 200,  # Average serving size
            'pack': 500,  # Average pack size
        }
        
        multiplier = conversions.get(unit.lower(), 100)  # Default to 100g
        return quantity * multiplier
    
    def generate_waste_projection(self, weeks=4):
        """
        Generate waste projection for next N weeks.
        """
        current_weekly = self.estimate_weekly_waste()
        projections = []
        
        for week in range(1, weeks + 1):
            # Simple projection based on current rate
            # Could be enhanced with ML predictions
            projected = {
                'week': week,
                'projected_grams': current_weekly['total_waste_grams'] * week,
                'projected_cost': current_weekly['total_waste_cost'] * week,
                'date': timezone.now().date() + timedelta(weeks=week)
            }
            projections.append(projected)
        
        return projections

