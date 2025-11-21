"""
SDG Impact Scoring Engine
Enhanced with AI-powered insights and specific actionable steps.
Evaluates user progress in waste reduction and nutrition improvement.
"""

import json
import os
from decimal import Decimal
from datetime import datetime, timedelta
from collections import defaultdict
from django.utils import timezone
from django.conf import settings
from django.db.models import Sum, Count, Avg, Q
from logs.models import FoodLog
from inventory.models import InventoryItem
from ai_analytics.models import SDGImpactScore
from ai_analytics.waste_estimator import WasteEstimator
from ai_analytics.ai_engine import AIConsumptionAnalyzer
from ai_analytics.expiration_predictor import ExpirationRiskPredictor


class SDGImpactScorer:
    """
    Enhanced SDG Impact Scoring Engine with AI-powered insights.
    Calculates comprehensive scores and provides specific, actionable recommendations.
    """
    
    def __init__(self, user):
        self.user = user
        self.profile = getattr(user, 'profile', None)
        self.waste_estimator = WasteEstimator(user)
        self.consumption_analyzer = AIConsumptionAnalyzer(user)
        self.expiration_predictor = ExpirationRiskPredictor(user)
    
    def calculate_sdg_score(self, week_start_date=None, use_ai=True):
        """
        Calculate comprehensive SDG impact score (0-100) with AI insights.
        
        Args:
            week_start_date: Start date of the week (defaults to current week)
            use_ai: Whether to use AI for insights generation
        
        Returns:
            Dictionary with scores, insights, and actionable steps
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
        
        # Get previous week for comparison
        previous_week_start = week_start_date - timedelta(days=7)
        previous_score_data = self._get_previous_week_score(previous_week_start)
        
        # Generate AI-powered insights
        if use_ai and self._has_openai_key():
            insights = self._generate_ai_insights(
                waste_score, nutrition_score, sustainability_score,
                previous_score_data
            )
        else:
            insights = self._generate_rule_based_insights(
                waste_score, nutrition_score, sustainability_score,
                previous_score_data
            )
        
        # Generate specific actionable steps with improvement estimates
        actionable_steps = self._generate_actionable_steps(
            waste_score, nutrition_score, sustainability_score,
            previous_score_data
        )
        
        return {
            'overall_score': Decimal(str(round(overall_score, 2))),
            'waste_reduction_score': Decimal(str(round(waste_score, 2))),
            'nutrition_score': Decimal(str(round(nutrition_score, 2))),
            'sustainability_score': Decimal(str(round(sustainability_score, 2))),
            'week_start_date': week_start_date,
            'insights': insights,
            'actionable_steps': actionable_steps,
            'improvement': self._calculate_improvement(overall_score, previous_score_data),
        }
    
    def _calculate_waste_reduction_score(self, week_start):
        """Calculate waste reduction score (0-100). Higher score = less waste."""
        weekly_waste = self.waste_estimator.estimate_weekly_waste()
        community_avg = self.waste_estimator.COMMUNITY_AVERAGE_WASTE['weekly_grams']
        waste_grams = weekly_waste['total_waste_grams']
        
        # Base score from waste amount (inverted - less waste = higher score)
        if waste_grams == 0:
            base_score = 100
        elif waste_grams <= community_avg * 0.3:  # Excellent
            base_score = 95
        elif waste_grams <= community_avg * 0.5:  # Very good
            base_score = 85
        elif waste_grams <= community_avg * 0.7:  # Good
            base_score = 75
        elif waste_grams <= community_avg:  # Average
            base_score = 60
        elif waste_grams <= community_avg * 1.5:  # Below average
            base_score = 45
        else:  # Poor
            base_score = 30
        
        # Bonus for improvement trend
        trend_bonus = self._calculate_waste_trend_bonus()
        
        # Penalty for expired items
        expired_count = InventoryItem.objects.filter(
            user=self.user,
            status='expired',
            expiration_date__gte=week_start
        ).count()
        expired_penalty = min(25, expired_count * 5)
        
        # Bonus for using expiring items
        expiring_used = InventoryItem.objects.filter(
            user=self.user,
            status='consumed',
            expiration_date__gte=week_start - timedelta(days=7),
            expiration_date__lte=week_start + timedelta(days=7)
        ).count()
        usage_bonus = min(10, expiring_used * 2)
        
        final_score = max(0, min(100, base_score + trend_bonus - expired_penalty + usage_bonus))
        return final_score
    
    def _calculate_nutrition_score(self, week_start):
        """Calculate nutrition score (0-100) based on balanced consumption."""
        # Check for category imbalances
        imbalances = self.consumption_analyzer.detect_category_imbalances()
        nutrient_gaps = self.consumption_analyzer.detect_nutrient_gaps()
        
        # Base score
        base_score = 100
        
        # Get consumption data
        week_logs = FoodLog.objects.filter(
            user=self.user,
            date_consumed__gte=week_start
        )
        
        # Penalty for imbalances
        for imbalance in imbalances:
            if imbalance['type'] == 'under_consumption':
                if imbalance['severity'] == 'high':
                    base_score -= 20
                elif imbalance['severity'] == 'medium':
                    base_score -= 12
                else:
                    base_score -= 6
            elif imbalance['type'] == 'over_consumption':
                if imbalance['severity'] == 'high':
                    base_score -= 10
                else:
                    base_score -= 5
        
        # Penalty for nutrient gaps
        for gap in nutrient_gaps:
            gap_pct = float(gap.get('gap_percentage', 0))
            if gap_pct > 50:
                base_score -= 25
            elif gap_pct > 30:
                base_score -= 15
            elif gap_pct > 15:
                base_score -= 8
            else:
                base_score -= 3
        
        # Bonus for variety (more categories = better)
        unique_categories = week_logs.values('category').distinct().count()
        if unique_categories >= 6:
            base_score += 15
        elif unique_categories >= 5:
            base_score += 10
        elif unique_categories >= 4:
            base_score += 5
        elif unique_categories >= 3:
            base_score += 2
        
        # Bonus for regular consumption
        if week_logs.count() >= 14:  # 2+ items per day
            base_score += 10
        elif week_logs.count() >= 7:  # 1+ item per day
            base_score += 5
        
        # Check for vegetable/fruit consumption (important for nutrition)
        veg_fruit_logs = week_logs.filter(category__in=['vegetable', 'fruit']).count()
        if veg_fruit_logs >= 10:
            base_score += 10
        elif veg_fruit_logs >= 5:
            base_score += 5
        
        return max(0, min(100, base_score))
    
    def _calculate_sustainability_score(self, week_start):
        """Calculate sustainability score (0-100) based on environmental impact."""
        base_score = 60
        
        # Check waste levels (low waste = more sustainable)
        weekly_waste = self.waste_estimator.estimate_weekly_waste()
        waste_grams = weekly_waste['total_waste_grams']
        community_avg = self.waste_estimator.COMMUNITY_AVERAGE_WASTE['weekly_grams']
        
        if waste_grams <= community_avg * 0.5:
            base_score += 20
        elif waste_grams <= community_avg * 0.7:
            base_score += 15
        elif waste_grams <= community_avg:
            base_score += 10
        elif waste_grams <= community_avg * 1.2:
            base_score += 5
        
        # Bonus for using expiring items (reduces waste)
        expiring_used = InventoryItem.objects.filter(
            user=self.user,
            status='consumed',
            expiration_date__gte=week_start - timedelta(days=7)
        ).count()
        if expiring_used >= 5:
            base_score += 15
        elif expiring_used >= 3:
            base_score += 10
        elif expiring_used >= 1:
            base_score += 5
        
        # Bonus for regular tracking (awareness = sustainability)
        week_logs = FoodLog.objects.filter(
            user=self.user,
            date_consumed__gte=week_start
        ).count()
        if week_logs >= 14:
            base_score += 10
        elif week_logs >= 7:
            base_score += 5
        
        # Bonus for meal planning (reduces waste)
        # Check if user has used meal optimizer (simplified check)
        # In production, would track actual meal plan usage
        
        return max(0, min(100, base_score))
    
    def _calculate_waste_trend_bonus(self):
        """Calculate bonus points for improving waste reduction trend."""
        # Compare last 2 weeks
        two_weeks_ago = timezone.now().date() - timedelta(days=14)
        one_week_ago = timezone.now().date() - timedelta(days=7)
        today = timezone.now().date()
        
        # Week 1 waste
        week1_expired = InventoryItem.objects.filter(
            user=self.user,
            status='expired',
            expiration_date__gte=two_weeks_ago,
            expiration_date__lt=one_week_ago
        ).count()
        
        # Week 2 waste
        week2_expired = InventoryItem.objects.filter(
            user=self.user,
            status='expired',
            expiration_date__gte=one_week_ago,
            expiration_date__lte=today
        ).count()
        
        # Calculate trend
        if week1_expired > 0:
            improvement = ((week1_expired - week2_expired) / week1_expired) * 100
            if improvement > 50:
                return 15  # Significant improvement
            elif improvement > 25:
                return 10  # Good improvement
            elif improvement > 0:
                return 5   # Some improvement
        elif week2_expired == 0 and week1_expired == 0:
            return 5  # Maintaining zero waste
        
        return 0
    
    def _get_previous_week_score(self, previous_week_start):
        """Get previous week's score for comparison."""
        try:
            previous_score = SDGImpactScore.objects.filter(
                user=self.user,
                week_start_date=previous_week_start
            ).first()
            
            if previous_score:
                return {
                    'overall_score': float(previous_score.overall_score),
                    'waste_score': float(previous_score.waste_reduction_score),
                    'nutrition_score': float(previous_score.nutrition_score),
                    'sustainability_score': float(previous_score.sustainability_score),
                }
        except:
            pass
        
        return None
    
    def _calculate_improvement(self, current_score, previous_data):
        """Calculate improvement from previous week."""
        if not previous_data:
            return {
                'overall_change': None,
                'waste_change': None,
                'nutrition_change': None,
                'sustainability_change': None,
                'trend': 'new',
            }
        
        current = float(current_score)
        previous = previous_data.get('overall_score', 0)
        
        change = current - previous
        percent_change = ((current - previous) / previous * 100) if previous > 0 else 0
        
        trend = 'improving' if change > 0 else 'declining' if change < 0 else 'stable'
        
        return {
            'overall_change': round(change, 2),
            'overall_percent_change': round(percent_change, 2),
            'waste_change': None,  # Can be calculated similarly
            'nutrition_change': None,
            'sustainability_change': None,
            'trend': trend,
        }
    
    def _generate_ai_insights(self, waste_score, nutrition_score, sustainability_score, previous_data):
        """Generate AI-powered insights using OpenAI."""
        try:
            import openai
            
            api_key = os.getenv('OPENAI_API_KEY') or getattr(settings, 'OPENAI_API_KEY', None)
            if not api_key:
                return self._generate_rule_based_insights(waste_score, nutrition_score, sustainability_score, previous_data)
            
            client = openai.OpenAI(api_key=api_key)
            
            # Build context
            context = self._build_insight_context(waste_score, nutrition_score, sustainability_score, previous_data)
            
            prompt = f"""Analyze this user's SDG impact scores and provide 3-5 specific insights:

Current Scores:
- Overall: {waste_score * 0.4 + nutrition_score * 0.35 + sustainability_score * 0.25:.1f}/100
- Waste Reduction: {waste_score:.1f}/100
- Nutrition: {nutrition_score:.1f}/100
- Sustainability: {sustainability_score:.1f}/100

Context:
{context}

Provide insights in JSON format:
{{
    "insights": [
        {{
            "type": "success|warning|info",
            "category": "waste|nutrition|sustainability|overall",
            "message": "Specific insight message",
            "impact": "high|medium|low",
            "improvement_potential": "X points or X%"
        }}
    ]
}}

Focus on:
1. What's working well
2. Areas needing improvement
3. Specific, actionable observations
4. Progress compared to previous week (if available)
"""
            
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {'role': 'system', 'content': 'You are an expert in sustainable food practices and SDG impact analysis. Provide specific, actionable insights.'},
                    {'role': 'user', 'content': prompt}
                ],
                temperature=0.7,
                max_tokens=400,
            )
            
            # Parse AI response
            response_text = response.choices[0].message.content.strip()
            
            # Try to extract JSON
            try:
                # Remove markdown code blocks if present
                if '```json' in response_text:
                    response_text = response_text.split('```json')[1].split('```')[0]
                elif '```' in response_text:
                    response_text = response_text.split('```')[1].split('```')[0]
                
                ai_data = json.loads(response_text)
                return ai_data.get('insights', [])
            except:
                # If JSON parsing fails, create structured insights from text
                return self._parse_ai_text_to_insights(response_text, waste_score, nutrition_score, sustainability_score)
                
        except Exception as e:
            # Fallback to rule-based
            return self._generate_rule_based_insights(waste_score, nutrition_score, sustainability_score, previous_data)
    
    def _build_insight_context(self, waste_score, nutrition_score, sustainability_score, previous_data):
        """Build context for AI insights."""
        context_parts = []
        
        # Waste context
        weekly_waste = self.waste_estimator.estimate_weekly_waste()
        expiring_items = InventoryItem.objects.filter(
            user=self.user,
            status='expiring_soon'
        )[:5]
        
        context_parts.append(f"Waste: {weekly_waste['total_waste_grams']:.0f}g/week, {len(expiring_items)} items expiring soon")
        
        # Nutrition context
        imbalances = self.consumption_analyzer.detect_category_imbalances()
        nutrient_gaps = self.consumption_analyzer.detect_nutrient_gaps()
        
        context_parts.append(f"Nutrition: {len(imbalances)} imbalances, {len(nutrient_gaps)} nutrient gaps detected")
        
        # Previous week comparison
        if previous_data:
            prev_overall = previous_data.get('overall_score', 0)
            current_overall = waste_score * 0.4 + nutrition_score * 0.35 + sustainability_score * 0.25
            change = current_overall - prev_overall
            context_parts.append(f"Previous week score: {prev_overall:.1f}, Change: {change:+.1f} points")
        
        # Consumption patterns
        week_start = timezone.now().date() - timedelta(days=7)
        week_logs = FoodLog.objects.filter(user=self.user, date_consumed__gte=week_start)
        categories = week_logs.values_list('category', flat=True)
        from collections import Counter
        top_cats = Counter(categories).most_common(3)
        context_parts.append(f"Top consumed categories: {', '.join([cat for cat, _ in top_cats])}")
        
        return "\n".join(context_parts)
    
    def _parse_ai_text_to_insights(self, text, waste_score, nutrition_score, sustainability_score):
        """Parse AI text response into structured insights."""
        insights = []
        
        # Simple parsing - look for key phrases
        text_lower = text.lower()
        
        if 'waste' in text_lower or 'waste reduction' in text_lower:
            insights.append({
                'type': 'warning' if waste_score < 70 else 'info',
                'category': 'waste',
                'message': text[:200] if len(text) > 200 else text,
                'impact': 'high' if waste_score < 60 else 'medium',
            })
        
        if 'nutrition' in text_lower or 'diet' in text_lower:
            insights.append({
                'type': 'info' if nutrition_score < 75 else 'success',
                'category': 'nutrition',
                'message': text[:200] if len(text) > 200 else text,
                'impact': 'high' if nutrition_score < 70 else 'medium',
            })
        
        return insights if insights else self._generate_rule_based_insights(waste_score, nutrition_score, sustainability_score, None)
    
    def _generate_rule_based_insights(self, waste_score, nutrition_score, sustainability_score, previous_data):
        """Generate rule-based insights with improvement tracking."""
        insights = []
        
        # Overall score insight
        overall = waste_score * 0.4 + nutrition_score * 0.35 + sustainability_score * 0.25
        
        if previous_data:
            prev_overall = previous_data.get('overall_score', 0)
            change = overall - prev_overall
            
            if change > 5:
                insights.append({
                    'type': 'success',
                    'category': 'overall',
                    'message': f'Great progress! Your score improved by {change:.1f} points this week.',
                    'impact': 'positive',
                    'improvement': f'+{change:.1f} points'
                })
            elif change < -5:
                insights.append({
                    'type': 'warning',
                    'category': 'overall',
                    'message': f'Your score decreased by {abs(change):.1f} points. Focus on the actionable steps below.',
                    'impact': 'high',
                    'improvement': f'{change:.1f} points'
                })
        
        # Waste insights
        if waste_score < 60:
            weekly_waste = self.waste_estimator.estimate_weekly_waste()
            insights.append({
                'type': 'warning',
                'category': 'waste',
                'message': f'Your waste reduction score is {waste_score:.1f}/100. You\'re wasting {weekly_waste["total_waste_grams"]:.0f}g per week (${weekly_waste["total_waste_cost"]:.2f}). Focus on using items before they expire.',
                'impact': 'high',
                'improvement_potential': '15-20 points'
            })
        elif waste_score >= 80:
            insights.append({
                'type': 'success',
                'category': 'waste',
                'message': f'Excellent waste management! Your score is {waste_score:.1f}/100. Keep up the great work!',
                'impact': 'positive',
            })
        
        # Nutrition insights
        imbalances = self.consumption_analyzer.detect_category_imbalances()
        nutrient_gaps = self.consumption_analyzer.detect_nutrient_gaps()
        
        if nutrition_score < 70:
            low_categories = [imb['category'] for imb in imbalances if imb.get('type') == 'under_consumption']
            if low_categories:
                insights.append({
                    'type': 'info',
                    'category': 'nutrition',
                    'message': f'Your nutrition score is {nutrition_score:.1f}/100. You\'re under-consuming: {", ".join(low_categories[:3])}. Adding these can boost your score significantly.',
                    'impact': 'high',
                    'improvement_potential': '10-15 points'
                })
            elif nutrient_gaps:
                gap_names = [gap['nutrient'] for gap in nutrient_gaps[:2]]
                insights.append({
                    'type': 'info',
                    'category': 'nutrition',
                    'message': f'Your nutrition score is {nutrition_score:.1f}/100. Nutrient gaps detected: {", ".join(gap_names)}. Focus on foods rich in these nutrients.',
                    'impact': 'medium',
                    'improvement_potential': '8-12 points'
                })
        elif nutrition_score >= 85:
            insights.append({
                'type': 'success',
                'category': 'nutrition',
                'message': f'Great nutrition balance! Your score is {nutrition_score:.1f}/100.',
                'impact': 'positive',
            })
        
        # Sustainability insights
        if sustainability_score < 70:
            insights.append({
                'type': 'info',
                'category': 'sustainability',
                'message': f'Your sustainability score is {sustainability_score:.1f}/100. Regular tracking and meal planning can help improve this.',
                'impact': 'medium',
                'improvement_potential': '10-15 points'
            })
        elif sustainability_score >= 85:
            insights.append({
                'type': 'success',
                'category': 'sustainability',
                'message': f'Excellent sustainability practices! Your score is {sustainability_score:.1f}/100.',
                'impact': 'positive',
            })
        
        return insights
    
    def _generate_actionable_steps(self, waste_score, nutrition_score, sustainability_score, previous_data):
        """Generate specific, actionable steps with improvement estimates."""
        steps = []
        
        # Waste reduction steps
        if waste_score < 75:
            expiring_items = InventoryItem.objects.filter(
                user=self.user,
                status='expiring_soon'
            )[:5]
            
            if expiring_items:
                items_list = ", ".join([item.item_name for item in expiring_items[:3]])
                steps.append({
                    'priority': 'high',
                    'action': f'Use expiring items first: {items_list}',
                    'expected_improvement': '12-18 points',
                    'category': 'waste',
                    'specific': True,
                })
            
            weekly_waste = self.waste_estimator.estimate_weekly_waste()
            if weekly_waste['total_waste_grams'] > 300:
                steps.append({
                    'priority': 'high',
                    'action': 'Plan meals around your inventory to reduce waste',
                    'expected_improvement': '10-15 points',
                    'category': 'waste',
                    'specific': False,
                })
            
            steps.append({
                'priority': 'medium',
                'action': 'Check expiration dates regularly and use FIFO (First In, First Out)',
                'expected_improvement': '8-12 points',
                'category': 'waste',
                'specific': False,
            })
        
        # Nutrition steps
        if nutrition_score < 80:
            imbalances = self.consumption_analyzer.detect_category_imbalances()
            nutrient_gaps = self.consumption_analyzer.detect_nutrient_gaps()
            
            # Find under-consumed categories
            under_consumed = [imb for imb in imbalances if imb.get('type') == 'under_consumption']
            
            if under_consumed:
                for imb in under_consumed[:2]:
                    category = imb.get('category', '').title()
                    steps.append({
                        'priority': 'high',
                        'action': f'Focus on adding more {category.lower()} to your meals',
                        'expected_improvement': '10-15 points',
                        'category': 'nutrition',
                        'specific': True,
                        'boost_percentage': '10-15%',
                    })
            
            # Nutrient-specific steps
            if nutrient_gaps:
                for gap in nutrient_gaps[:2]:
                    nutrient = gap.get('nutrient', 'nutrients')
                    gap_pct = float(gap.get('gap_percentage', 0))
                    if gap_pct > 30:
                        improvement_points = min(15, int(gap_pct * 0.3))
                        steps.append({
                            'priority': 'high',
                            'action': f'Increase {nutrient} intake - you have a {gap_pct:.0f}% gap',
                            'expected_improvement': f'{improvement_points} points',
                            'category': 'nutrition',
                            'specific': True,
                            'boost_percentage': f'{improvement_points}%',
                        })
            
            # General variety step
            week_start = timezone.now().date() - timedelta(days=7)
            week_logs = FoodLog.objects.filter(user=self.user, date_consumed__gte=week_start)
            unique_cats = week_logs.values('category').distinct().count()
            
            if unique_cats < 4:
                steps.append({
                    'priority': 'medium',
                    'action': 'Add more variety to your diet - aim for 5+ different food categories per week',
                    'expected_improvement': '8-12 points',
                    'category': 'nutrition',
                    'specific': False,
                    'boost_percentage': '8-12%',
                })
        
        # Sustainability steps
        if sustainability_score < 75:
            week_start = timezone.now().date() - timedelta(days=7)
            week_logs = FoodLog.objects.filter(user=self.user, date_consumed__gte=week_start).count()
            
            if week_logs < 7:
                steps.append({
                    'priority': 'medium',
                    'action': 'Log your food consumption daily for better tracking and awareness',
                    'expected_improvement': '5-10 points',
                    'category': 'sustainability',
                    'specific': False,
                })
            
            steps.append({
                'priority': 'medium',
                'action': 'Use the Meal Optimizer to plan sustainable, waste-reducing meals',
                'expected_improvement': '8-12 points',
                'category': 'sustainability',
                'specific': False,
            })
        
        # Sort by priority
        steps.sort(key=lambda x: 0 if x['priority'] == 'high' else 1)
        
        return steps[:6]  # Return top 6 steps
    
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
    
    def get_weekly_insights(self, weeks=4):
        """Get weekly insights for the last N weeks."""
        today = timezone.now().date()
        insights = []
        
        for week_num in range(weeks):
            week_start = today - timedelta(days=(today.weekday() + (week_num * 7)))
            score_data = self.calculate_sdg_score(week_start_date=week_start)
            
            insights.append({
                'week_start': week_start,
                'week_number': week_num + 1,
                'overall_score': float(score_data['overall_score']),
                'waste_score': float(score_data['waste_reduction_score']),
                'nutrition_score': float(score_data['nutrition_score']),
                'sustainability_score': float(score_data['sustainability_score']),
                'insights': score_data['insights'],
            })
        
        return insights
    
    def get_historical_scores(self, limit=12):
        """Get historical SDG scores."""
        return SDGImpactScore.objects.filter(
            user=self.user
        ).order_by('-week_start_date')[:limit]
    
    def _has_openai_key(self):
        """Check if OpenAI API key is available."""
        api_key = os.getenv('OPENAI_API_KEY') or getattr(settings, 'OPENAI_API_KEY', None)
        return api_key is not None
