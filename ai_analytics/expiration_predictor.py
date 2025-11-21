"""
AI Expiration Risk Prediction System
Predicts expiry risks based on consumption frequency, category, and seasonality.
Combines FIFO with AI ranking scores and generates alerts.
"""

from decimal import Decimal
from datetime import datetime, timedelta
from collections import defaultdict
from django.utils import timezone
from django.db.models import Avg, Count, Q
from inventory.models import InventoryItem
from logs.models import FoodLog


class ExpirationRiskPredictor:
    """
    Advanced expiration risk prediction with consumption patterns and seasonality.
    """
    
    # Category-based expiration risk factors (base rates)
    CATEGORY_EXPIRATION_RATES = {
        'fruit': {'base_days': 7, 'risk_multiplier': 1.5, 'seasonal_sensitive': True},
        'vegetable': {'base_days': 10, 'risk_multiplier': 1.3, 'seasonal_sensitive': True},
        'dairy': {'base_days': 5, 'risk_multiplier': 1.4, 'seasonal_sensitive': False},
        'meat': {'base_days': 3, 'risk_multiplier': 1.6, 'seasonal_sensitive': False},
        'grain': {'base_days': 30, 'risk_multiplier': 0.8, 'seasonal_sensitive': False},
        'beverage': {'base_days': 14, 'risk_multiplier': 1.0, 'seasonal_sensitive': False},
        'snack': {'base_days': 60, 'risk_multiplier': 0.7, 'seasonal_sensitive': False},
        'frozen': {'base_days': 90, 'risk_multiplier': 0.5, 'seasonal_sensitive': False},
        'canned': {'base_days': 365, 'risk_multiplier': 0.3, 'seasonal_sensitive': False},
        'other': {'base_days': 14, 'risk_multiplier': 1.0, 'seasonal_sensitive': False},
    }
    
    # Seasonality factors (dummy rules)
    # Assuming Northern Hemisphere seasons
    SEASONAL_FACTORS = {
        'spring': {'fruit': 1.2, 'vegetable': 1.1, 'dairy': 1.0, 'meat': 1.0},
        'summer': {'fruit': 1.5, 'vegetable': 1.3, 'dairy': 1.2, 'meat': 1.1},  # Warmer = faster expiration
        'autumn': {'fruit': 1.1, 'vegetable': 1.0, 'dairy': 1.0, 'meat': 1.0},
        'winter': {'fruit': 0.9, 'vegetable': 0.8, 'dairy': 0.9, 'meat': 1.0},  # Colder = slower expiration
    }
    
    # Risk thresholds
    RISK_THRESHOLDS = {
        'critical': 80,  # Critical risk - immediate action needed
        'high': 60,      # High risk - action within 24 hours
        'medium': 40,    # Medium risk - action within 3 days
        'low': 20,       # Low risk - monitor
    }
    
    def __init__(self, user):
        self.user = user
        self.profile = getattr(user, 'profile', None)
        self.inventory_items = InventoryItem.objects.filter(
            user=user
        ).exclude(status='consumed')
        self.food_logs = FoodLog.objects.filter(user=user)
        self.household_size = self.profile.household_size if self.profile else 1
    
    def predict_expiration_risks(self, days_ahead=7):
        """
        Predict expiration risks for all inventory items.
        Returns prioritized list with AI scores.
        """
        today = timezone.now().date()
        target_date = today + timedelta(days=days_ahead)
        
        # Get items with expiration dates
        items_with_dates = self.inventory_items.filter(
            expiration_date__isnull=False,
            expiration_date__lte=target_date
        ).exclude(status='consumed')
        
        # Calculate consumption patterns
        consumption_patterns = self._analyze_consumption_patterns()
        
        # Get current season
        current_season = self._get_current_season()
        
        predictions = []
        
        for item in items_with_dates:
            risk_score = self._calculate_risk_score(
                item, 
                consumption_patterns, 
                current_season
            )
            
            # Calculate AI ranking score (combines FIFO + risk factors)
            ai_ranking_score = self._calculate_ai_ranking_score(item, risk_score)
            
            # Determine priority level
            priority = self._determine_priority(risk_score)
            
            # Generate reasoning
            reasoning = self._generate_reasoning(
                item, 
                risk_score, 
                consumption_patterns, 
                current_season
            )
            
            predictions.append({
                'inventory_item': item,
                'item_name': item.item_name,
                'category': item.category,
                'expiration_date': item.expiration_date,
                'days_until_expiry': (item.expiration_date - today).days,
                'risk_score': risk_score,
                'ai_ranking_score': ai_ranking_score,
                'priority': priority,
                'reasoning': reasoning,
                'recommended_action': self._get_recommended_action(risk_score, item),
            })
        
        # Sort by AI ranking score (highest risk first)
        predictions.sort(key=lambda x: x['ai_ranking_score'], reverse=True)
        
        return predictions
    
    def _analyze_consumption_patterns(self):
        """
        Analyze user's consumption patterns by category.
        """
        thirty_days_ago = timezone.now().date() - timedelta(days=30)
        recent_logs = self.food_logs.filter(date_consumed__gte=thirty_days_ago)
        
        patterns = defaultdict(lambda: {
            'total_consumed': 0,
            'consumption_days': 0,
            'avg_daily': 0,
            'frequency': 0,  # How often consumed (days between consumptions)
        })
        
        # Group by category and date
        category_dates = defaultdict(list)
        for log in recent_logs:
            category_dates[log.category].append(log.date_consumed)
            patterns[log.category]['total_consumed'] += float(log.quantity)
        
        # Calculate averages
        for category, dates in category_dates.items():
            unique_dates = sorted(set(dates))
            patterns[category]['consumption_days'] = len(unique_dates)
            
            if len(unique_dates) > 1:
                # Calculate average days between consumptions
                intervals = [
                    (unique_dates[i] - unique_dates[i-1]).days 
                    for i in range(1, len(unique_dates))
                ]
                patterns[category]['frequency'] = sum(intervals) / len(intervals) if intervals else 0
            else:
                patterns[category]['frequency'] = 30  # Only consumed once in 30 days
            
            # Average daily consumption
            if patterns[category]['consumption_days'] > 0:
                patterns[category]['avg_daily'] = (
                    patterns[category]['total_consumed'] / patterns[category]['consumption_days']
                )
        
        return patterns
    
    def _get_current_season(self):
        """Get current season (dummy implementation)."""
        month = timezone.now().month
        
        if month in [12, 1, 2]:
            return 'winter'
        elif month in [3, 4, 5]:
            return 'spring'
        elif month in [6, 7, 8]:
            return 'summer'
        else:
            return 'autumn'
    
    def _calculate_risk_score(self, item, consumption_patterns, season):
        """
        Calculate expiration risk score (0-100).
        Higher score = higher risk.
        """
        if not item.expiration_date:
            return 0
        
        today = timezone.now().date()
        days_until_expiry = (item.expiration_date - today).days
        
        # Base risk from time until expiration
        if days_until_expiry <= 0:
            time_risk = 100  # Already expired
        elif days_until_expiry <= 1:
            time_risk = 90
        elif days_until_expiry <= 3:
            time_risk = 75
        elif days_until_expiry <= 7:
            time_risk = 60
        else:
            time_risk = max(20, 60 - (days_until_expiry - 7) * 2)
        
        # Category-based risk adjustment
        category_data = self.CATEGORY_EXPIRATION_RATES.get(
            item.category, 
            {'base_days': 14, 'risk_multiplier': 1.0, 'seasonal_sensitive': False}
        )
        
        category_risk = time_risk * category_data['risk_multiplier']
        
        # Seasonality adjustment
        if category_data['seasonal_sensitive']:
            seasonal_factor = self.SEASONAL_FACTORS.get(season, {}).get(item.category, 1.0)
            category_risk *= seasonal_factor
        
        # Consumption pattern adjustment
        consumption_risk = 0
        pattern = consumption_patterns.get(item.category, {})
        
        if pattern.get('avg_daily', 0) > 0:
            current_quantity = float(item.quantity)
            days_to_consume = current_quantity / pattern['avg_daily']
            
            # If it takes longer to consume than days until expiry, increase risk
            if days_to_consume > days_until_expiry:
                consumption_risk = min(30, (days_to_consume - days_until_expiry) * 5)
            
            # If consumption frequency is low, increase risk
            if pattern.get('frequency', 0) > 7:  # Consumed less than once per week
                consumption_risk += 10
        
        # Household size adjustment
        household_adjustment = 0
        if self.household_size > 1:
            household_adjustment = -5 * (self.household_size - 1)  # Larger households consume faster
        
        # Calculate final risk score
        final_risk = category_risk + consumption_risk + household_adjustment
        final_risk = max(0, min(100, final_risk))
        
        return round(final_risk, 2)
    
    def _calculate_ai_ranking_score(self, item, risk_score):
        """
        Calculate AI ranking score combining FIFO and risk factors.
        Higher score = higher priority for consumption.
        """
        today = timezone.now().date()
        
        # FIFO component (older items get higher priority)
        if item.purchase_date:
            days_since_purchase = (today - item.purchase_date).days
            fifo_score = min(50, days_since_purchase * 2)  # Max 50 points
        else:
            fifo_score = 0
        
        # Risk score component (higher risk = higher priority)
        risk_component = risk_score * 0.5  # Max 50 points
        
        # Expiration proximity bonus
        if item.expiration_date:
            days_until = (item.expiration_date - today).days
            if days_until <= 0:
                proximity_bonus = 50  # Expired
            elif days_until <= 1:
                proximity_bonus = 40
            elif days_until <= 3:
                proximity_bonus = 30
            elif days_until <= 7:
                proximity_bonus = 20
            else:
                proximity_bonus = max(0, 20 - days_until)
        else:
            proximity_bonus = 0
        
        # Category urgency bonus
        category_data = self.CATEGORY_EXPIRATION_RATES.get(item.category, {})
        urgency_bonus = (1 - category_data.get('risk_multiplier', 1.0) / 2) * 10
        
        # Final AI ranking score
        ai_score = fifo_score + risk_component + proximity_bonus + urgency_bonus
        
        return round(ai_score, 2)
    
    def _determine_priority(self, risk_score):
        """Determine priority level based on risk score."""
        if risk_score >= self.RISK_THRESHOLDS['critical']:
            return 'critical'
        elif risk_score >= self.RISK_THRESHOLDS['high']:
            return 'high'
        elif risk_score >= self.RISK_THRESHOLDS['medium']:
            return 'medium'
        else:
            return 'low'
    
    def _generate_reasoning(self, item, risk_score, consumption_patterns, season):
        """Generate human-readable reasoning for the risk prediction."""
        today = timezone.now().date()
        days_until = (item.expiration_date - today).days if item.expiration_date else 0
        
        reasons = []
        
        # Time-based reasoning
        if days_until <= 0:
            reasons.append("Item has already expired")
        elif days_until <= 1:
            reasons.append(f"Expires in {days_until} day - urgent action needed")
        elif days_until <= 3:
            reasons.append(f"Expires in {days_until} days - high priority")
        else:
            reasons.append(f"Expires in {days_until} days")
        
        # Category reasoning
        category_data = self.CATEGORY_EXPIRATION_RATES.get(item.category, {})
        if category_data.get('seasonal_sensitive'):
            seasonal_factor = self.SEASONAL_FACTORS.get(season, {}).get(item.category, 1.0)
            if seasonal_factor > 1.0:
                reasons.append(f"{item.category.title()} items expire faster in {season}")
        
        # Consumption pattern reasoning
        pattern = consumption_patterns.get(item.category, {})
        if pattern.get('avg_daily', 0) > 0:
            current_quantity = float(item.quantity)
            days_to_consume = current_quantity / pattern['avg_daily']
            
            if days_to_consume > days_until:
                reasons.append(
                    f"Based on your consumption rate ({pattern['avg_daily']:.2f} {item.unit}/day), "
                    f"you need {days_to_consume:.1f} days to consume this item"
                )
        
        if pattern.get('frequency', 0) > 7:
            reasons.append(f"You consume {item.category} items infrequently (every {pattern['frequency']:.1f} days on average)")
        
        return " | ".join(reasons)
    
    def _get_recommended_action(self, risk_score, item):
        """Get recommended action based on risk score."""
        priority = self._determine_priority(risk_score)
        
        actions = {
            'critical': f"Use {item.item_name} immediately or freeze/preserve it today",
            'high': f"Plan to use {item.item_name} within 24 hours",
            'medium': f"Prioritize {item.item_name} in your meal planning for the next 3 days",
            'low': f"Monitor {item.item_name} - still safe but plan consumption soon",
        }
        
        return actions.get(priority, "Monitor this item")
    
    def get_high_risk_alerts(self, limit=10):
        """
        Get high-risk items that need immediate attention.
        Returns alerts for in-app display.
        """
        predictions = self.predict_expiration_risks(days_ahead=7)
        
        alerts = []
        for pred in predictions:
            if pred['priority'] in ['critical', 'high']:
                alerts.append({
                    'type': pred['priority'],
                    'item': pred['inventory_item'],
                    'item_name': pred['item_name'],
                    'expiration_date': pred['expiration_date'],
                    'days_until_expiry': pred['days_until_expiry'],
                    'risk_score': pred['risk_score'],
                    'recommended_action': pred['recommended_action'],
                    'reasoning': pred['reasoning'],
                    'url': f"/inventory/{pred['inventory_item'].id}/",
                })
        
        return alerts[:limit]
    
    def get_consumption_priority_list(self):
        """
        Get prioritized list of items for consumption (FIFO + AI ranking).
        """
        predictions = self.predict_expiration_risks(days_ahead=14)
        
        # Return top 10 items prioritized for consumption
        return predictions[:10]
    
    def get_category_risk_summary(self):
        """Get risk summary by category."""
        predictions = self.predict_expiration_risks(days_ahead=7)
        
        category_risks = defaultdict(lambda: {
            'total_items': 0,
            'high_risk_items': 0,
            'avg_risk': 0,
            'total_risk': 0,
        })
        
        for pred in predictions:
            category = pred['category']
            category_risks[category]['total_items'] += 1
            category_risks[category]['total_risk'] += pred['risk_score']
            
            if pred['priority'] in ['critical', 'high']:
                category_risks[category]['high_risk_items'] += 1
        
        # Calculate averages
        for category, data in category_risks.items():
            if data['total_items'] > 0:
                data['avg_risk'] = data['total_risk'] / data['total_items']
        
        return dict(category_risks)

