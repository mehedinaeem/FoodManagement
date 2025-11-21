"""
Advanced AI Analytics Engine for Food Management
Implements consumption pattern analysis, waste prediction, and meal optimization.
"""

import json
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from decimal import Decimal
from django.utils import timezone
from django.db.models import Sum, Count, Avg, Q
from logs.models import FoodLog
from inventory.models import InventoryItem, FoodItem
from ai_analytics.models import (
    ConsumptionPattern, WastePrediction, NutrientGap, SDGImpactScore
)


class AIConsumptionAnalyzer:
    """
    Advanced AI-powered consumption pattern analyzer.
    """
    
    # Nutrient database (simplified - in production, use comprehensive database)
    NUTRIENT_DATABASE = {
        'vegetable': {'vitamin_c': 50, 'fiber': 30, 'vitamin_a': 40, 'iron': 10},
        'fruit': {'vitamin_c': 80, 'fiber': 25, 'vitamin_a': 20, 'potassium': 60},
        'dairy': {'calcium': 90, 'protein': 40, 'vitamin_d': 30, 'vitamin_b12': 50},
        'meat': {'protein': 80, 'iron': 60, 'vitamin_b12': 70, 'zinc': 50},
        'grain': {'fiber': 40, 'iron': 20, 'vitamin_b': 30, 'protein': 15},
    }
    
    # Recommended daily values (simplified)
    DAILY_REQUIREMENTS = {
        'vitamin_c': 90,
        'fiber': 25,
        'vitamin_a': 900,
        'iron': 18,
        'calcium': 1000,
        'protein': 50,
        'vitamin_d': 20,
        'vitamin_b12': 2.4,
        'potassium': 3500,
        'zinc': 11,
        'vitamin_b': 1.5,
    }
    
    def __init__(self, user):
        self.user = user
        self.food_logs = FoodLog.objects.filter(user=user)
        self.inventory_items = InventoryItem.objects.filter(user=user)
        self.profile = getattr(user, 'profile', None)
    
    def analyze_weekly_trends(self):
        """
        Identify weekly consumption trends (e.g., high fruit intake on weekends).
        Returns JSON data suitable for heatmap visualization.
        """
        # Get logs from last 4 weeks
        four_weeks_ago = timezone.now().date() - timedelta(days=28)
        recent_logs = self.food_logs.filter(date_consumed__gte=four_weeks_ago)
        
        # Group by day of week and category
        trends = defaultdict(lambda: defaultdict(int))
        
        for log in recent_logs:
            day_of_week = log.date_consumed.weekday()  # 0=Monday, 6=Sunday
            day_name = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'][day_of_week]
            trends[day_name][log.category] += float(log.quantity)
        
        # Identify patterns
        patterns = []
        for day, categories in trends.items():
            if categories:
                top_category = max(categories.items(), key=lambda x: x[1])
                if top_category[1] > sum(categories.values()) * 0.4:  # More than 40% of day's consumption
                    patterns.append({
                        'day': day,
                        'category': top_category[0],
                        'percentage': (top_category[1] / sum(categories.values())) * 100,
                        'description': f"High {top_category[0]} consumption on {day}s"
                    })
        
        # Create heatmap data
        heatmap_data = {}
        for day in ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']:
            heatmap_data[day] = dict(trends.get(day, {}))
        
        return {
            'patterns': patterns,
            'heatmap_data': heatmap_data,
            'summary': self._generate_trend_summary(patterns)
        }
    
    def detect_category_imbalances(self):
        """
        Detect over-consumption or under-consumption in categories.
        """
        # Get consumption from last 30 days
        thirty_days_ago = timezone.now().date() - timedelta(days=30)
        recent_logs = self.food_logs.filter(date_consumed__gte=thirty_days_ago)
        
        # Calculate category distribution
        category_totals = Counter()
        total_quantity = 0
        
        for log in recent_logs:
            category_totals[log.category] += float(log.quantity)
            total_quantity += float(log.quantity)
        
        if total_quantity == 0:
            return []
        
        # Expected distribution (balanced diet guidelines)
        expected_distribution = {
            'vegetable': 0.30,  # 30%
            'fruit': 0.20,      # 20%
            'grain': 0.25,      # 25%
            'dairy': 0.10,      # 10%
            'meat': 0.10,       # 10%
            'other': 0.05,      # 5%
        }
        
        imbalances = []
        for category, expected_pct in expected_distribution.items():
            actual_pct = (category_totals[category] / total_quantity) * 100 if total_quantity > 0 else 0
            expected_quantity = total_quantity * expected_pct
            
            if actual_pct < expected_pct * 0.5:  # Less than 50% of expected
                imbalances.append({
                    'category': category,
                    'type': 'under_consumption',
                    'actual': actual_pct,
                    'expected': expected_pct * 100,
                    'gap': expected_pct * 100 - actual_pct,
                    'severity': 'high' if actual_pct < expected_pct * 0.3 else 'medium',
                    'description': f"Low {category} consumption ({actual_pct:.1f}% vs {expected_pct*100:.1f}% recommended)"
                })
            elif actual_pct > expected_pct * 1.5:  # More than 150% of expected
                imbalances.append({
                    'category': category,
                    'type': 'over_consumption',
                    'actual': actual_pct,
                    'expected': expected_pct * 100,
                    'gap': actual_pct - expected_pct * 100,
                    'severity': 'medium',
                    'description': f"High {category} consumption ({actual_pct:.1f}% vs {expected_pct*100:.1f}% recommended)"
                })
        
        return imbalances
    
    def predict_waste_risk(self, days_ahead=7):
        """
        Predict items likely to be wasted in the next 3-7 days using user patterns.
        """
        predictions = []
        today = timezone.now().date()
        target_date = today + timedelta(days=days_ahead)
        
        # Get items that might expire
        at_risk_items = self.inventory_items.filter(
            expiration_date__lte=target_date,
            expiration_date__gte=today
        ).exclude(status='consumed')
        
        # Analyze consumption patterns for each category
        thirty_days_ago = today - timedelta(days=30)
        recent_logs = self.food_logs.filter(date_consumed__gte=thirty_days_ago)
        
        # Calculate average consumption rate per category
        category_consumption = defaultdict(list)
        for log in recent_logs:
            category_consumption[log.category].append(float(log.quantity))
        
        category_avg_consumption = {
            cat: sum(quantities) / len(quantities) if quantities else 0
            for cat, quantities in category_consumption.items()
        }
        
        for item in at_risk_items:
            # Calculate waste probability
            days_until_expiry = (item.expiration_date - today).days
            
            # Base risk from expiration proximity
            if days_until_expiry <= 1:
                base_risk = 90
            elif days_until_expiry <= 3:
                base_risk = 70
            else:
                base_risk = 50
            
            # Adjust based on consumption patterns
            avg_consumption = category_avg_consumption.get(item.category, 0)
            current_quantity = float(item.quantity)
            
            # If consumption rate is low, increase risk
            if avg_consumption > 0:
                days_to_consume = current_quantity / avg_consumption
                if days_to_consume > days_until_expiry:
                    base_risk += 20
            
            # Adjust for household size
            if self.profile and self.profile.household_size > 1:
                base_risk -= 10  # Larger households consume faster
            
            base_risk = max(0, min(100, base_risk))
            
            reasoning = f"Item expires in {days_until_expiry} days. "
            if avg_consumption > 0:
                reasoning += f"Based on your consumption patterns, you typically consume {avg_consumption:.2f} {item.unit} per day. "
            reasoning += f"Current quantity: {current_quantity} {item.unit}."
            
            predictions.append({
                'inventory_item': item,
                'item_name': item.item_name,
                'category': item.category,
                'predicted_waste_probability': Decimal(str(base_risk)),
                'predicted_waste_date': item.expiration_date,
                'reasoning': reasoning,
                'days_until_expiry': days_until_expiry
            })
        
        return predictions
    
    def detect_nutrient_gaps(self):
        """
        Analyze consumption history and predict nutrient deficiencies.
        """
        # Get consumption from last 30 days
        thirty_days_ago = timezone.now().date() - timedelta(days=30)
        recent_logs = self.food_logs.filter(date_consumed__gte=thirty_days_ago)
        
        # Calculate nutrient intake
        nutrient_totals = defaultdict(float)
        days_tracked = len(set(log.date_consumed for log in recent_logs)) or 1
        
        for log in recent_logs:
            category = log.category
            quantity = float(log.quantity)
            
            if category in self.NUTRIENT_DATABASE:
                nutrients = self.NUTRIENT_DATABASE[category]
                for nutrient, value_per_unit in nutrients.items():
                    nutrient_totals[nutrient] += (value_per_unit * quantity) / 100  # Normalize
        
        # Calculate average daily intake
        daily_averages = {
            nutrient: total / days_tracked
            for nutrient, total in nutrient_totals.items()
        }
        
        # Detect gaps
        gaps = []
        for nutrient, daily_avg in daily_averages.items():
            if nutrient in self.DAILY_REQUIREMENTS:
                required = self.DAILY_REQUIREMENTS[nutrient]
                gap_pct = max(0, ((required - daily_avg) / required) * 100) if required > 0 else 0
                
                if gap_pct > 20:  # More than 20% gap
                    # Find foods that can fill this gap
                    suggested_foods = self._find_foods_for_nutrient(nutrient)
                    
                    gaps.append({
                        'nutrient_name': nutrient.replace('_', ' ').title(),
                        'current_level': Decimal(str(daily_avg)),
                        'recommended_level': Decimal(str(required)),
                        'gap_percentage': Decimal(str(gap_pct)),
                        'suggested_foods': suggested_foods
                    })
        
        return gaps
    
    def _find_foods_for_nutrient(self, nutrient):
        """Find foods high in a specific nutrient."""
        high_nutrient_foods = []
        for category, nutrients in self.NUTRIENT_DATABASE.items():
            if nutrient in nutrients and nutrients[nutrient] > 50:
                # Get food items from database
                foods = FoodItem.objects.filter(category=category)[:3]
                high_nutrient_foods.extend([food.name for food in foods])
        return high_nutrient_foods[:5]
    
    def _generate_trend_summary(self, patterns):
        """Generate human-readable summary of trends."""
        if not patterns:
            return "No significant weekly trends detected. Your consumption is fairly consistent."
        
        summaries = []
        for pattern in patterns[:3]:
            summaries.append(pattern['description'])
        
        return " | ".join(summaries)
    
    def generate_heatmap_json(self):
        """Generate JSON data for heatmap visualization."""
        trends = self.analyze_weekly_trends()
        return json.dumps(trends['heatmap_data'], indent=2)
    
    def get_category_distribution(self):
        """
        Get category distribution for visualization.
        Returns data suitable for pie/bar charts.
        """
        thirty_days_ago = timezone.now().date() - timedelta(days=30)
        recent_logs = self.food_logs.filter(date_consumed__gte=thirty_days_ago)
        
        category_totals = Counter()
        for log in recent_logs:
            category_totals[log.category] += float(log.quantity)
        
        total = sum(category_totals.values()) or 1
        
        distribution = {
            'labels': list(category_totals.keys()),
            'values': [float(v) for v in category_totals.values()],
            'percentages': [(v / total * 100) for v in category_totals.values()],
            'total': total
        }
        
        return distribution
    
    def get_weekly_consumption_chart_data(self):
        """
        Get weekly consumption data formatted for Chart.js.
        """
        trends = self.analyze_weekly_trends()
        heatmap = trends['heatmap_data']
        
        # Get all unique categories
        all_categories = set()
        for day_data in heatmap.values():
            all_categories.update(day_data.keys())
        all_categories = sorted(list(all_categories))
        
        # Format for Chart.js
        chart_data = {
            'labels': ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'],
            'datasets': []
        }
        
        # Color palette
        colors = [
            'rgba(75, 192, 192, 0.6)',
            'rgba(255, 99, 132, 0.6)',
            'rgba(54, 162, 235, 0.6)',
            'rgba(255, 206, 86, 0.6)',
            'rgba(153, 102, 255, 0.6)',
            'rgba(255, 159, 64, 0.6)',
            'rgba(199, 199, 199, 0.6)',
        ]
        
        for idx, category in enumerate(all_categories):
            dataset = {
                'label': category.title(),
                'data': [heatmap.get(day, {}).get(category, 0) for day in chart_data['labels']],
                'backgroundColor': colors[idx % len(colors)],
                'borderColor': colors[idx % len(colors)].replace('0.6', '1'),
                'borderWidth': 2
            }
            chart_data['datasets'].append(dataset)
        
        return chart_data

