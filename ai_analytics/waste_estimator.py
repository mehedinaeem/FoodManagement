"""
AI Waste Estimation Model
Estimates wasted food and money from patterns with ML support.
Enhanced with predictive formulas and optional ML API integration.
"""

import os
import json
from decimal import Decimal
from datetime import datetime, timedelta
from collections import defaultdict
from django.utils import timezone
from django.conf import settings
from django.db.models import Sum, Count, Avg, Q
from inventory.models import InventoryItem
from logs.models import FoodLog


class WasteEstimator:
    """
    Advanced waste estimation with pattern analysis, projections, and ML support.
    """
    
    # Enhanced waste rates by category (percentage)
    CATEGORY_WASTE_RATES = {
        'vegetable': 0.25,  # 25% waste rate
        'fruit': 0.20,      # 20% waste rate
        'dairy': 0.15,      # 15% waste rate
        'meat': 0.10,       # 10% waste rate
        'grain': 0.05,      # 5% waste rate
        'beverage': 0.08,   # 8% waste rate
        'snack': 0.12,      # 12% waste rate
        'frozen': 0.03,     # 3% waste rate
        'canned': 0.02,     # 2% waste rate
        'other': 0.15,      # 15% waste rate
    }
    
    # Average cost per unit by category (enhanced)
    AVG_COST_PER_UNIT = {
        'vegetable': 2.50,
        'fruit': 3.00,
        'dairy': 4.00,
        'meat': 8.00,
        'grain': 2.00,
        'beverage': 2.50,
        'snack': 3.50,
        'frozen': 3.00,
        'canned': 2.00,
        'other': 3.00,
    }
    
    # Enhanced community average waste (dummy dataset with variations)
    COMMUNITY_AVERAGE_WASTE = {
        'weekly_grams': 500,  # grams per week
        'weekly_cost': 15.00,  # dollars per week
        'monthly_grams': 2000,
        'monthly_cost': 60.00,
        'yearly_grams': 24000,
        'yearly_cost': 720.00,
        'by_category': {
            'vegetable': {'grams': 125, 'cost': 3.75},
            'fruit': {'grams': 100, 'cost': 3.00},
            'dairy': {'grams': 75, 'cost': 3.00},
            'meat': {'grams': 50, 'cost': 4.00},
            'grain': {'grams': 25, 'cost': 0.50},
            'other': {'grams': 125, 'cost': 0.75},
        }
    }
    
    def __init__(self, user):
        self.user = user
        self.inventory_items = InventoryItem.objects.filter(user=user)
        self.food_logs = FoodLog.objects.filter(user=user)
        self.profile = getattr(user, 'profile', None)
        self.household_size = self.profile.household_size if self.profile else 1
    
    def estimate_weekly_waste(self, use_ml=False):
        """
        Estimate wasted food for the current week.
        Returns grams and cost estimates.
        """
        if use_ml and self._has_ml_api():
            return self._estimate_with_ml('weekly')
        
        week_start = timezone.now().date() - timedelta(days=7)
        today = timezone.now().date()
        
        # Get expired items this week
        expired_items = self.inventory_items.filter(
            status='expired',
            expiration_date__gte=week_start,
            expiration_date__lte=today
        )
        
        # Calculate actual waste from expired items
        expired_waste_grams = Decimal('0.00')
        expired_waste_cost = Decimal('0.00')
        expired_by_category = defaultdict(lambda: {'grams': 0, 'cost': 0, 'count': 0})
        
        for item in expired_items:
            grams = self._convert_to_grams(float(item.quantity), item.unit)
            expired_waste_grams += Decimal(str(grams))
            
            avg_cost = self.AVG_COST_PER_UNIT.get(item.category, 3.00)
            cost = Decimal(str(avg_cost * float(item.quantity)))
            expired_waste_cost += cost
            
            expired_by_category[item.category]['grams'] += float(grams)
            expired_by_category[item.category]['cost'] += float(cost)
            expired_by_category[item.category]['count'] += 1
        
        # Estimate pattern-based waste (items likely to be wasted)
        pattern_waste_grams = Decimal('0.00')
        pattern_waste_cost = Decimal('0.00')
        pattern_by_category = defaultdict(lambda: {'grams': 0, 'cost': 0})
        
        # Analyze consumption patterns
        consumption_patterns = self._analyze_consumption_patterns()
        
        # Get items purchased this week
        purchased_items = self.inventory_items.filter(
            purchase_date__gte=week_start
        ).exclude(status='consumed')
        
        for item in purchased_items:
            category = item.category
            waste_rate = self.CATEGORY_WASTE_RATES.get(category, 0.15)
            
            # Adjust waste rate based on consumption patterns
            pattern = consumption_patterns.get(category, {})
            if pattern.get('frequency', 0) > 7:  # Consumed infrequently
                waste_rate *= 1.2  # Increase waste rate by 20%
            
            # Check if item is expiring soon
            if item.expiration_date:
                days_until = (item.expiration_date - today).days
                if days_until <= 3:
                    waste_rate *= 1.3  # Increase waste rate if expiring soon
            
            grams = self._convert_to_grams(float(item.quantity), item.unit)
            estimated_waste = Decimal(str(grams * waste_rate))
            pattern_waste_grams += estimated_waste
            
            avg_cost = self.AVG_COST_PER_UNIT.get(category, 3.00)
            cost = Decimal(str(avg_cost * float(item.quantity) * waste_rate))
            pattern_waste_cost += cost
            
            pattern_by_category[category]['grams'] += float(estimated_waste)
            pattern_by_category[category]['cost'] += float(cost)
        
        total_waste_grams = expired_waste_grams + pattern_waste_grams
        total_waste_cost = expired_waste_cost + pattern_waste_cost
        
        return {
            'expired_waste_grams': float(expired_waste_grams),
            'expired_waste_cost': float(expired_waste_cost),
            'pattern_waste_grams': float(pattern_waste_grams),
            'pattern_waste_cost': float(pattern_waste_cost),
            'total_waste_grams': float(total_waste_grams),
            'total_waste_cost': float(total_waste_cost),
            'week_start': week_start,
            'by_category': {
                'expired': dict(expired_by_category),
                'pattern': dict(pattern_by_category),
            }
        }
    
    def estimate_monthly_waste(self, use_ml=False):
        """
        Estimate wasted food for the current month with projections.
        """
        if use_ml and self._has_ml_api():
            return self._estimate_with_ml('monthly')
        
        month_start = timezone.now().date() - timedelta(days=30)
        today = timezone.now().date()
        
        # Actual expired items this month
        expired_items = self.inventory_items.filter(
            status='expired',
            expiration_date__gte=month_start,
            expiration_date__lte=today
        )
        
        actual_waste_grams = Decimal('0.00')
        actual_waste_cost = Decimal('0.00')
        
        for item in expired_items:
            grams = self._convert_to_grams(float(item.quantity), item.unit)
            actual_waste_grams += Decimal(str(grams))
            
            avg_cost = self.AVG_COST_PER_UNIT.get(item.category, 3.00)
            cost = Decimal(str(avg_cost * float(item.quantity)))
            actual_waste_cost += cost
        
        # Project based on weekly average with trend analysis
        weekly_estimate = self.estimate_weekly_waste()
        
        # Calculate trend (improving or worsening)
        trend_factor = self._calculate_waste_trend()
        
        # Project monthly waste (4 weeks with trend adjustment)
        base_monthly_grams = weekly_estimate['total_waste_grams'] * 4
        base_monthly_cost = weekly_estimate['total_waste_cost'] * 4
        
        projected_monthly_grams = base_monthly_grams * trend_factor
        projected_monthly_cost = base_monthly_cost * trend_factor
        
        return {
            'actual_waste_grams': float(actual_waste_grams),
            'actual_waste_cost': float(actual_waste_cost),
            'projected_waste_grams': float(projected_monthly_grams),
            'projected_waste_cost': float(projected_monthly_cost),
            'month_start': month_start,
            'trend_factor': trend_factor,
            'trend_direction': 'improving' if trend_factor < 1.0 else 'worsening' if trend_factor > 1.0 else 'stable',
        }
    
    def _analyze_consumption_patterns(self):
        """Analyze consumption patterns for waste prediction."""
        thirty_days_ago = timezone.now().date() - timedelta(days=30)
        recent_logs = self.food_logs.filter(date_consumed__gte=thirty_days_ago)
        
        patterns = defaultdict(lambda: {
            'total_consumed': 0,
            'consumption_days': 0,
            'frequency': 0,
            'avg_daily': 0,
        })
        
        category_dates = defaultdict(list)
        for log in recent_logs:
            category_dates[log.category].append(log.date_consumed)
            patterns[log.category]['total_consumed'] += float(log.quantity)
        
        for category, dates in category_dates.items():
            unique_dates = sorted(set(dates))
            patterns[category]['consumption_days'] = len(unique_dates)
            
            if len(unique_dates) > 1:
                intervals = [
                    (unique_dates[i] - unique_dates[i-1]).days 
                    for i in range(1, len(unique_dates))
                ]
                patterns[category]['frequency'] = sum(intervals) / len(intervals) if intervals else 0
            else:
                patterns[category]['frequency'] = 30
            
            if patterns[category]['consumption_days'] > 0:
                patterns[category]['avg_daily'] = (
                    patterns[category]['total_consumed'] / patterns[category]['consumption_days']
                )
        
        return patterns
    
    def _calculate_waste_trend(self):
        """
        Calculate waste trend factor (1.0 = stable, <1.0 = improving, >1.0 = worsening).
        """
        # Compare last 2 weeks
        two_weeks_ago = timezone.now().date() - timedelta(days=14)
        one_week_ago = timezone.now().date() - timedelta(days=7)
        today = timezone.now().date()
        
        # Week 1 waste
        week1_expired = self.inventory_items.filter(
            status='expired',
            expiration_date__gte=two_weeks_ago,
            expiration_date__lt=one_week_ago
        )
        
        week1_waste = sum(
            self._convert_to_grams(float(item.quantity), item.unit)
            for item in week1_expired
        )
        
        # Week 2 waste
        week2_expired = self.inventory_items.filter(
            status='expired',
            expiration_date__gte=one_week_ago,
            expiration_date__lte=today
        )
        
        week2_waste = sum(
            self._convert_to_grams(float(item.quantity), item.unit)
            for item in week2_expired
        )
        
        # Calculate trend
        if week1_waste > 0:
            trend_ratio = week2_waste / week1_waste
            # Smooth the trend (0.9 to 1.1 range)
            return min(1.1, max(0.9, trend_ratio))
        else:
            return 1.0  # No data, assume stable
    
    def compare_to_community(self):
        """
        Compare user's waste to community averages with detailed breakdown.
        """
        weekly = self.estimate_weekly_waste()
        monthly = self.estimate_monthly_waste()
        
        # Weekly comparison
        weekly_diff_grams = weekly['total_waste_grams'] - self.COMMUNITY_AVERAGE_WASTE['weekly_grams']
        weekly_diff_cost = weekly['total_waste_cost'] - self.COMMUNITY_AVERAGE_WASTE['weekly_cost']
        
        weekly_pct_diff = (
            (weekly_diff_grams / self.COMMUNITY_AVERAGE_WASTE['weekly_grams']) * 100
            if self.COMMUNITY_AVERAGE_WASTE['weekly_grams'] > 0 else 0
        )
        
        # Monthly comparison
        monthly_diff_grams = monthly['projected_waste_grams'] - self.COMMUNITY_AVERAGE_WASTE['monthly_grams']
        monthly_diff_cost = monthly['projected_waste_cost'] - self.COMMUNITY_AVERAGE_WASTE['monthly_cost']
        
        monthly_pct_diff = (
            (monthly_diff_grams / self.COMMUNITY_AVERAGE_WASTE['monthly_grams']) * 100
            if self.COMMUNITY_AVERAGE_WASTE['monthly_grams'] > 0 else 0
        )
        
        # Category comparison
        category_comparison = {}
        user_by_category = weekly.get('by_category', {}).get('expired', {})
        user_by_category.update(weekly.get('by_category', {}).get('pattern', {}))
        
        for category, community_data in self.COMMUNITY_AVERAGE_WASTE['by_category'].items():
            user_data = user_by_category.get(category, {'grams': 0, 'cost': 0})
            category_comparison[category] = {
                'user_grams': user_data.get('grams', 0),
                'community_grams': community_data['grams'],
                'user_cost': user_data.get('cost', 0),
                'community_cost': community_data['cost'],
                'difference_grams': user_data.get('grams', 0) - community_data['grams'],
                'difference_cost': user_data.get('cost', 0) - community_data['cost'],
            }
        
        return {
            'weekly': {
                'user_grams': weekly['total_waste_grams'],
                'community_grams': self.COMMUNITY_AVERAGE_WASTE['weekly_grams'],
                'user_cost': weekly['total_waste_cost'],
                'community_cost': self.COMMUNITY_AVERAGE_WASTE['weekly_cost'],
                'difference_grams': weekly_diff_grams,
                'difference_cost': weekly_diff_cost,
                'percentage_difference': weekly_pct_diff,
                'status': 'better' if weekly_pct_diff < 0 else 'worse' if weekly_pct_diff > 0 else 'equal',
            },
            'monthly': {
                'user_grams': monthly['projected_waste_grams'],
                'community_grams': self.COMMUNITY_AVERAGE_WASTE['monthly_grams'],
                'user_cost': monthly['projected_waste_cost'],
                'community_cost': self.COMMUNITY_AVERAGE_WASTE['monthly_cost'],
                'difference_grams': monthly_diff_grams,
                'difference_cost': monthly_diff_cost,
                'percentage_difference': monthly_pct_diff,
                'status': 'better' if monthly_pct_diff < 0 else 'worse' if monthly_pct_diff > 0 else 'equal',
            },
            'by_category': category_comparison,
        }
    
    def generate_waste_projection(self, weeks=12, use_ml=False):
        """
        Generate waste projection for next N weeks with trend analysis.
        """
        if use_ml and self._has_ml_api():
            return self._project_with_ml(weeks)
        
        current_weekly = self.estimate_weekly_waste()
        trend_factor = self._calculate_waste_trend()
        
        projections = []
        cumulative_grams = 0
        cumulative_cost = 0
        
        for week in range(1, weeks + 1):
            # Apply trend factor (gradual improvement/worsening)
            week_trend = 1.0 + (trend_factor - 1.0) * (week / weeks) * 0.5  # Gradual change
            
            projected_grams = current_weekly['total_waste_grams'] * week_trend
            projected_cost = current_weekly['total_waste_cost'] * week_trend
            
            cumulative_grams += projected_grams
            cumulative_cost += projected_cost
            
            projections.append({
                'week': week,
                'projected_grams': projected_grams,
                'projected_cost': projected_cost,
                'cumulative_grams': cumulative_grams,
                'cumulative_cost': cumulative_cost,
                'date': timezone.now().date() + timedelta(weeks=week),
                'trend_factor': week_trend,
            })
        
        return projections
    
    def estimate_yearly_waste(self):
        """Estimate yearly waste projection."""
        monthly = self.estimate_monthly_waste()
        
        return {
            'projected_grams': monthly['projected_waste_grams'] * 12,
            'projected_cost': monthly['projected_waste_cost'] * 12,
            'community_grams': self.COMMUNITY_AVERAGE_WASTE['yearly_grams'],
            'community_cost': self.COMMUNITY_AVERAGE_WASTE['yearly_cost'],
        }
    
    def _convert_to_grams(self, quantity, unit):
        """Convert various units to grams."""
        conversions = {
            'kg': 1000,
            'g': 1,
            'lb': 453.592,
            'oz': 28.3495,
            'l': 1000,
            'ml': 1,
            'cup': 240,
            'piece': 150,
            'serving': 200,
            'pack': 500,
        }
        
        multiplier = conversions.get(unit.lower(), 100)
        return quantity * multiplier
    
    def _has_ml_api(self):
        """Check if ML API is available (e.g., custom ML service)."""
        # In production, check for ML API endpoint
        ml_api_url = os.getenv('ML_WASTE_API_URL') or getattr(settings, 'ML_WASTE_API_URL', None)
        return ml_api_url is not None
    
    def _estimate_with_ml(self, period='weekly'):
        """
        Estimate waste using ML API (if available).
        Falls back to rule-based if API unavailable.
        """
        try:
            import requests
            
            ml_api_url = os.getenv('ML_WASTE_API_URL') or getattr(settings, 'ML_WASTE_API_URL', None)
            if not ml_api_url:
                return self.estimate_weekly_waste() if period == 'weekly' else self.estimate_monthly_waste()
            
            # Prepare data for ML API
            user_data = {
                'user_id': self.user.id,
                'household_size': self.household_size,
                'period': period,
                'inventory_count': self.inventory_items.count(),
                'recent_logs_count': self.food_logs.filter(
                    date_consumed__gte=timezone.now().date() - timedelta(days=30)
                ).count(),
            }
            
            # Call ML API
            response = requests.post(
                ml_api_url,
                json=user_data,
                timeout=5
            )
            
            if response.status_code == 200:
                ml_result = response.json()
                return {
                    'total_waste_grams': ml_result.get('waste_grams', 0),
                    'total_waste_cost': ml_result.get('waste_cost', 0),
                    'method': 'ML_API',
                    'confidence': ml_result.get('confidence', 0.8),
                }
            else:
                # Fallback to rule-based
                return self.estimate_weekly_waste() if period == 'weekly' else self.estimate_monthly_waste()
                
        except Exception as e:
            # Fallback to rule-based
            return self.estimate_weekly_waste() if period == 'weekly' else self.estimate_monthly_waste()
    
    def _project_with_ml(self, weeks):
        """Generate projections using ML API."""
        try:
            import requests
            
            ml_api_url = os.getenv('ML_WASTE_API_URL') or getattr(settings, 'ML_WASTE_API_URL', None)
            if not ml_api_url:
                return self.generate_waste_projection(weeks, use_ml=False)
            
            user_data = {
                'user_id': self.user.id,
                'weeks': weeks,
            }
            
            response = requests.post(
                f"{ml_api_url}/project",
                json=user_data,
                timeout=5
            )
            
            if response.status_code == 200:
                ml_projections = response.json().get('projections', [])
                return ml_projections
            else:
                return self.generate_waste_projection(weeks, use_ml=False)
                
        except Exception as e:
            return self.generate_waste_projection(weeks, use_ml=False)
