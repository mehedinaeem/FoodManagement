"""
SDG Impact Scoring Engine
Evaluates user progress in waste reduction and nutrition improvement.
"""

from decimal import Decimal
from datetime import datetime, timedelta
from django.utils import timezone
from django.db.models import Sum, Count, Avg, Q
from logs.models import FoodLog
from inventory.models import InventoryItem
from ai_analytics.models import SDGImpactScore
from ai_analytics.waste_estimator import WasteEstimator
from ai_analytics.ai_engine import AIConsumptionAnalyzer


class SDGImpactScorer:
    """
    Calculates SDG impact scores based on waste reduction and nutrition.
    """
    
    def __init__(self, user):
        self.user = user
        self.profile = getattr(user, 'profile', None)
        self.waste_estimator = WasteEstimator(user)
        self.consumption_analyzer = AIConsumptionAnalyzer(user)
    
    def calculate_sdg_score(self, week_start_date=None):
        """
        Calculate comprehensive SDG impact score (0-100).
        """
        if week_start_date is None:
            # Get start of current week (Monday)
            today = timezone.now().date()
            days_since_monday = today.weekday()
            week_start_date = today - timedelta(days=days_since_monday)
        
        # Calculate component scores
        waste_score = self._calculate_waste_reduction_score(week_start_date)
        nutrition_score = self._calculate_nutrition_score(week_start_date)
        sustainability_score = self._calculate_sustainability_score(week_start_date)
        
        # Weighted overall score
        overall_score = (
            waste_score * 0.40 +  # 40% weight on waste reduction
            nutrition_score * 0.35 +  # 35% weight on nutrition
            sustainability_score * 0.25  # 25% weight on sustainability
        )
        
        # Generate insights
        insights = self._generate_insights(waste_score, nutrition_score, sustainability_score)
        
        # Generate actionable steps
        actionable_steps = self._generate_actionable_steps(
            waste_score, nutrition_score, sustainability_score
        )
        
        return {
            'overall_score': Decimal(str(round(overall_score, 2))),
            'waste_reduction_score': Decimal(str(round(waste_score, 2))),
            'nutrition_score': Decimal(str(round(nutrition_score, 2))),
            'sustainability_score': Decimal(str(round(sustainability_score, 2))),
            'week_start_date': week_start_date,
            'insights': insights,
            'actionable_steps': actionable_steps,
        }
    
    def _calculate_waste_reduction_score(self, week_start):
        """
        Calculate waste reduction score (0-100).
        Higher score = less waste.
        """
        weekly_waste = self.waste_estimator.estimate_weekly_waste()
        community_avg = self.waste_estimator.COMMUNITY_AVERAGE_WASTE['weekly_grams']
        
        # Base score from waste amount
        if weekly_waste['total_waste_grams'] == 0:
            base_score = 100
        elif weekly_waste['total_waste_grams'] <= community_avg * 0.5:
            base_score = 90
        elif weekly_waste['total_waste_grams'] <= community_avg:
            base_score = 75
        elif weekly_waste['total_waste_grams'] <= community_avg * 1.5:
            base_score = 60
        else:
            base_score = 40
        
        # Bonus for improvement trend
        trend_bonus = self._calculate_waste_trend_bonus()
        
        # Penalty for expired items
        expired_penalty = 0
        expired_count = InventoryItem.objects.filter(
            user=self.user,
            status='expired',
            expiration_date__gte=week_start
        ).count()
        if expired_count > 0:
            expired_penalty = min(20, expired_count * 5)
        
        final_score = max(0, min(100, base_score + trend_bonus - expired_penalty))
        return final_score
    
    def _calculate_nutrition_score(self, week_start):
        """
        Calculate nutrition score (0-100).
        Based on balanced consumption and nutrient gaps.
        """
        # Check for category imbalances
        imbalances = self.consumption_analyzer.detect_category_imbalances()
        nutrient_gaps = self.consumption_analyzer.detect_nutrient_gaps()
        
        # Base score
        base_score = 100
        
        # Penalty for imbalances
        for imbalance in imbalances:
            if imbalance['type'] == 'under_consumption':
                if imbalance['severity'] == 'high':
                    base_score -= 15
                else:
                    base_score -= 8
            elif imbalance['type'] == 'over_consumption':
                base_score -= 5
        
        # Penalty for nutrient gaps
        for gap in nutrient_gaps:
            gap_pct = float(gap['gap_percentage'])
            if gap_pct > 50:
                base_score -= 20
            elif gap_pct > 30:
                base_score -= 12
            else:
                base_score -= 6
        
        # Bonus for variety
        week_logs = FoodLog.objects.filter(
            user=self.user,
            date_consumed__gte=week_start
        )
        unique_categories = week_logs.values('category').distinct().count()
        if unique_categories >= 5:
            base_score += 10
        elif unique_categories >= 3:
            base_score += 5
        
        return max(0, min(100, base_score))
    
    def _calculate_sustainability_score(self, week_start):
        """
        Calculate sustainability score (0-100).
        Based on consumption patterns and environmental impact.
        """
        base_score = 70
        
        # Check for local/seasonal consumption (simplified)
        # In production, would check location and season
        
        # Bonus for meal planning (reduces waste)
        weekly_waste = self.waste_estimator.estimate_weekly_waste()
        if weekly_waste['total_waste_grams'] < 200:  # Low waste
            base_score += 15
        
        # Bonus for using inventory efficiently
        expiring_used = InventoryItem.objects.filter(
            user=self.user,
            status='consumed',
            expiration_date__gte=week_start - timedelta(days=7)
        ).count()
        if expiring_used > 0:
            base_score += 10
        
        # Check consumption frequency (regular tracking = better)
        week_logs = FoodLog.objects.filter(
            user=self.user,
            date_consumed__gte=week_start
        ).count()
        if week_logs >= 7:  # Daily logging
            base_score += 10
        elif week_logs >= 4:
            base_score += 5
        
        return max(0, min(100, base_score))
    
    def _calculate_waste_trend_bonus(self):
        """Calculate bonus points for improving waste reduction trend."""
        # Compare last 2 weeks
        two_weeks_ago = timezone.now().date() - timedelta(days=14)
        one_week_ago = timezone.now().date() - timedelta(days=7)
        
        # This is simplified - in production would calculate actual trends
        return 5  # Small bonus for now
    
    def _generate_insights(self, waste_score, nutrition_score, sustainability_score):
        """Generate AI insights based on scores."""
        insights = []
        
        if waste_score < 60:
            insights.append({
                'type': 'warning',
                'category': 'waste',
                'message': f'Your waste reduction score is {waste_score:.1f}/100. Focus on using items before they expire.',
                'impact': 'high'
            })
        
        if nutrition_score < 70:
            insights.append({
                'type': 'info',
                'category': 'nutrition',
                'message': f'Your nutrition score is {nutrition_score:.1f}/100. Consider adding more variety to your diet.',
                'impact': 'medium'
            })
        
        if sustainability_score > 80:
            insights.append({
                'type': 'success',
                'category': 'sustainability',
                'message': f'Great job! Your sustainability score is {sustainability_score:.1f}/100.',
                'impact': 'positive'
            })
        
        return insights
    
    def _generate_actionable_steps(self, waste_score, nutrition_score, sustainability_score):
        """Generate actionable steps to improve scores."""
        steps = []
        
        if waste_score < 70:
            steps.append({
                'priority': 'high',
                'action': 'Review expiring items and plan meals around them',
                'expected_improvement': '10-15 points',
                'category': 'waste'
            })
            steps.append({
                'priority': 'medium',
                'action': 'Use meal planning to reduce food waste',
                'expected_improvement': '5-10 points',
                'category': 'waste'
            })
        
        if nutrition_score < 75:
            steps.append({
                'priority': 'high',
                'action': 'Add more vegetables to your meals',
                'expected_improvement': '10%',
                'category': 'nutrition'
            })
            steps.append({
                'priority': 'medium',
                'action': 'Balance your food categories',
                'expected_improvement': '8%',
                'category': 'nutrition'
            })
        
        if sustainability_score < 75:
            steps.append({
                'priority': 'medium',
                'action': 'Log your consumption daily for better tracking',
                'expected_improvement': '5-8 points',
                'category': 'sustainability'
            })
        
        return steps
    
    def save_weekly_score(self, week_start_date=None):
        """Calculate and save SDG score for the week."""
        score_data = self.calculate_sdg_score(week_start_date)
        
        # Save or update score
        score, created = SDGImpactScore.objects.update_or_create(
            user=self.user,
            week_start_date=score_data['week_start_date'],
            defaults={
                'overall_score': score_data['overall_score'],
                'waste_reduction_score': score_data['waste_reduction_score'],
                'nutrition_score': score_data['nutrition_score'],
                'sustainability_score': score_data['sustainability_score'],
                'insights': score_data['insights'],
                'actionable_steps': score_data['actionable_steps'],
            }
        )
        
        return score

