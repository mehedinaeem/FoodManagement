from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
import json

from .ai_engine import AIConsumptionAnalyzer
from .meal_optimizer import MealOptimizer
from .waste_estimator import WasteEstimator
from .sdg_scorer import SDGImpactScorer
from .chatbot import NourishBot
from .ocr_processor import OCRProcessor
from .expiration_predictor import ExpirationRiskPredictor
from .models import ConsumptionPattern, WastePrediction, NutrientGap, SDGImpactScore, ChatSession
from uploads.models import Upload
from inventory.models import InventoryItem


@login_required
def ai_analytics_dashboard(request):
    """
    Main AI Analytics Dashboard showing all AI insights.
    """
    analyzer = AIConsumptionAnalyzer(request.user)
    waste_estimator = WasteEstimator(request.user)
    sdg_scorer = SDGImpactScorer(request.user)
    
    # Get weekly trends
    weekly_trends = analyzer.analyze_weekly_trends()
    
    # Get category imbalances
    imbalances = analyzer.detect_category_imbalances()
    
    # Get waste predictions
    waste_predictions = analyzer.predict_waste_risk(days_ahead=7)
    
    # Get nutrient gaps
    nutrient_gaps = analyzer.detect_nutrient_gaps()
    
    # Get waste estimates
    weekly_waste = waste_estimator.estimate_weekly_waste()
    monthly_waste = waste_estimator.estimate_monthly_waste()
    community_comparison = waste_estimator.compare_to_community()
    
    # Get SDG score
    sdg_score = sdg_scorer.calculate_sdg_score()
    
    # Get latest SDG score from database
    latest_sdg_score = SDGImpactScore.objects.filter(
        user=request.user
    ).order_by('-week_start_date').first()
    
    context = {
        'weekly_trends': weekly_trends,
        'imbalances': imbalances,
        'waste_predictions': waste_predictions[:5],  # Top 5
        'nutrient_gaps': nutrient_gaps,
        'weekly_waste': weekly_waste,
        'monthly_waste': monthly_waste,
        'community_comparison': community_comparison,
        'sdg_score': sdg_score,
        'latest_sdg_score': latest_sdg_score,
        'heatmap_json': analyzer.generate_heatmap_json(),
    }
    
    return render(request, 'ai_analytics/dashboard.html', context)


@login_required
def consumption_patterns(request):
    """
    Display detailed consumption pattern analysis.
    """
    analyzer = AIConsumptionAnalyzer(request.user)
    
    weekly_trends = analyzer.analyze_weekly_trends()
    imbalances = analyzer.detect_category_imbalances()
    category_distribution = analyzer.get_category_distribution()
    weekly_chart_data = analyzer.get_weekly_consumption_chart_data()
    
    # Save patterns to database
    for imbalance in imbalances:
        ConsumptionPattern.objects.update_or_create(
            user=request.user,
            pattern_type=imbalance['type'],
            category=imbalance['category'],
            defaults={
                'description': imbalance['description'],
                'severity': imbalance['severity'],
                'data': imbalance
            }
        )
    
    # Prepare week days and heatmap data for template
    week_days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    
    # Prepare heatmap data in a more template-friendly format
    heatmap_matrix = []
    all_categories = category_distribution.get('labels', [])
    
    # Find max value for normalization
    max_value = 0
    for day in week_days:
        day_data = weekly_trends['heatmap_data'].get(day, {})
        for category in all_categories:
            value = day_data.get(category, 0)
            if value > max_value:
                max_value = value
    
    for day in week_days:
        day_data = weekly_trends['heatmap_data'].get(day, {})
        row = {'day': day, 'values': []}
        for category in all_categories:
            value = day_data.get(category, 0)
            # Calculate opacity (0.1 to 1.0)
            opacity = 0.1 if max_value == 0 else min(1.0, 0.1 + (value / max_value * 0.9))
            row['values'].append({
                'category': category, 
                'value': value,
                'opacity': opacity
            })
        heatmap_matrix.append(row)
    
    context = {
        'weekly_trends': weekly_trends,
        'imbalances': imbalances,
        'category_distribution': category_distribution,
        'weekly_chart_data': json.dumps(weekly_chart_data),
        'week_days': week_days,
        'heatmap_matrix': heatmap_matrix,
        'heatmap_json': analyzer.generate_heatmap_json(),
    }
    
    return render(request, 'ai_analytics/consumption_patterns.html', context)


@login_required
def waste_analysis(request):
    """
    Display comprehensive waste analysis with projections and comparisons.
    """
    analyzer = AIConsumptionAnalyzer(request.user)
    waste_estimator = WasteEstimator(request.user)
    
    # Check if ML should be used
    use_ml = request.GET.get('use_ml', 'false') == 'true'
    
    # Get predictions
    waste_predictions = analyzer.predict_waste_risk(days_ahead=7)
    
    # Save predictions to database
    for pred in waste_predictions:
        WastePrediction.objects.update_or_create(
            user=request.user,
            inventory_item=pred.get('inventory_item'),
            item_name=pred['item_name'],
            predicted_waste_date=pred['predicted_waste_date'],
            defaults={
                'category': pred['category'],
                'predicted_waste_probability': pred['predicted_waste_probability'],
                'reasoning': pred['reasoning']
            }
        )
    
    # Get waste estimates
    weekly_waste = waste_estimator.estimate_weekly_waste(use_ml=use_ml)
    monthly_waste = waste_estimator.estimate_monthly_waste(use_ml=use_ml)
    community_comparison = waste_estimator.compare_to_community()
    
    # Get projections (12 weeks)
    weeks_ahead = int(request.GET.get('weeks', 12))
    waste_projection = waste_estimator.generate_waste_projection(weeks=weeks_ahead, use_ml=use_ml)
    
    # Get yearly estimate
    yearly_waste = waste_estimator.estimate_yearly_waste()
    
    context = {
        'waste_predictions': waste_predictions,
        'weekly_waste': weekly_waste,
        'monthly_waste': monthly_waste,
        'community_comparison': community_comparison,
        'waste_projection': waste_projection,
        'yearly_waste': yearly_waste,
        'weeks_ahead': weeks_ahead,
        'use_ml': use_ml,
        'has_ml': waste_estimator._has_ml_api(),
    }
    
    return render(request, 'ai_analytics/waste_analysis.html', context)


@login_required
def meal_optimizer(request):
    """
    Display meal optimization interface.
    """
    optimizer = MealOptimizer(request.user)
    
    if request.method == 'POST':
        budget_limit = request.POST.get('budget_limit')
        use_llm = request.POST.get('use_llm', 'false') == 'true'
        
        if budget_limit:
            budget_limit = float(budget_limit)
        else:
            budget_limit = None
        
        meal_plan = optimizer.optimize_weekly_meal_plan(
            budget_limit=budget_limit,
            use_llm=use_llm
        )
        
        context = {
            'meal_plan': meal_plan,
            'budget_limit': budget_limit,
            'optimization_method': meal_plan.get('optimization_method', 'Rule-Based'),
        }
        
        return render(request, 'ai_analytics/meal_plan_result.html', context)
    
    # Get user's budget preference
    budget_map = {'low': 50, 'medium': 75, 'high': 100}
    profile = getattr(request.user, 'profile', None)
    budget_range = profile.budget_range if profile else 'medium'
    default_budget = budget_map.get(budget_range, 75)
    
    # Check if LLM is available
    has_openai = optimizer._has_openai_key()
    
    context = {
        'default_budget': default_budget,
        'has_openai': has_openai,
    }
    
    return render(request, 'ai_analytics/meal_optimizer.html', context)


@login_required
def sdg_impact(request):
    """
    Display SDG Impact Score and insights.
    """
    scorer = SDGImpactScorer(request.user)
    
    # Calculate current score
    current_score = scorer.calculate_sdg_score()
    
    # Get historical scores
    historical_scores = SDGImpactScore.objects.filter(
        user=request.user
    ).order_by('-week_start_date')[:12]  # Last 12 weeks
    
    # Save current score
    saved_score = scorer.save_weekly_score()
    
    context = {
        'current_score': current_score,
        'saved_score': saved_score,
        'historical_scores': historical_scores,
    }
    
    return render(request, 'ai_analytics/sdg_impact.html', context)


@login_required
def chatbot(request):
    """
    NourishBot chatbot interface.
    """
    session_id = request.GET.get('session_id')
    bot = NourishBot(request.user, session_id=session_id)
    
    if request.method == 'POST':
        user_message = request.POST.get('message', '')
        use_ai = request.POST.get('use_ai', 'false') == 'true'
        
        if user_message:
            response = bot.chat(user_message, use_ai=use_ai)
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                # AJAX request
                return JsonResponse({
                    'response': response,
                    'session_id': bot.session_id
                })
    
    # Get conversation history
    history = bot.get_conversation_history(limit=50)
    
    context = {
        'session_id': bot.session_id,
        'conversation_history': history,
        'has_openai': bot._has_openai_key(),
    }
    
    return render(request, 'ai_analytics/chatbot.html', context)


@login_required
def process_ocr(request, upload_id):
    """
    Process uploaded image with OCR.
    Supports automatic addition for high-confidence extractions.
    """
    upload = get_object_or_404(Upload, id=upload_id, user=request.user)
    processor = OCRProcessor(upload)
    
    use_google_vision = request.GET.get('use_google', 'false') == 'true'
    auto_add = request.GET.get('auto_add', 'false') == 'true'
    
    # Process OCR
    result = processor.extract_food_data(use_google_vision=use_google_vision)
    
    # Handle automatic addition for high-confidence extractions
    if auto_add and result.get('success') and result.get('confidence', 0) >= 80:
        extracted = result.get('extracted_data', {})
        create_result = processor.create_inventory_item(
            request.user, 
            extracted, 
            auto_add=True
        )
        
        if create_result.get('auto_added'):
            messages.success(request, 'Item automatically added to inventory!')
            return redirect('inventory:detail', pk=create_result['item'].id)
    
    # Handle POST (user confirmation)
    if request.method == 'POST':
        if result.get('success'):
            extracted = result.get('extracted_data', {})
            
            # Get form data (user may have edited)
            item_name = request.POST.get('item_name', extracted.get('item_name', ''))
            quantity = request.POST.get('quantity', extracted.get('quantity', 1))
            unit = request.POST.get('unit', extracted.get('unit', 'piece'))
            category = request.POST.get('category', extracted.get('category', 'other'))
            expiration_date_str = request.POST.get('expiration_date', '')
            
            # Parse expiration date
            expiration_date = None
            if expiration_date_str:
                try:
                    expiration_date = datetime.strptime(expiration_date_str, '%Y-%m-%d').date()
                except:
                    expiration_date = extracted.get('expiration_date')
            else:
                expiration_date = extracted.get('expiration_date')
            
            # Create inventory item
            try:
                item = InventoryItem.objects.create(
                    user=request.user,
                    item_name=item_name,
                    quantity=Decimal(str(quantity)),
                    unit=unit,
                    category=category,
                    purchase_date=timezone.now().date(),
                    expiration_date=expiration_date,
                )
                item.update_status()
                
                # Associate upload
                upload.associated_inventory = item
                upload.save()
                
                messages.success(request, 'Item added to inventory successfully!')
                return redirect('inventory:detail', pk=item.id)
            except Exception as e:
                messages.error(request, f'Error creating inventory item: {str(e)}')
    
    context = {
        'upload': upload,
        'result': result,
        'extracted_data': result.get('extracted_data', {}),
        'confidence': result.get('confidence', 0),
        'is_partial': result.get('is_partial', False),
        'missing_fields': result.get('missing_fields', []),
        'has_google_vision': processor._has_google_vision_key(),
    }
    
    return render(request, 'ai_analytics/ocr_result.html', context)


@login_required
@require_http_methods(["GET"])
def get_heatmap_data(request):
    """
    API endpoint for heatmap data (JSON).
    """
    analyzer = AIConsumptionAnalyzer(request.user)
    trends = analyzer.analyze_weekly_trends()
    
    return JsonResponse(trends['heatmap_data'])


@login_required
def expiration_risks(request):
    """
    Display AI expiration risk predictions with prioritization.
    """
    predictor = ExpirationRiskPredictor(request.user)
    
    # Get predictions
    days_ahead = int(request.GET.get('days', 7))
    predictions = predictor.predict_expiration_risks(days_ahead=days_ahead)
    
    # Get alerts
    alerts = predictor.get_high_risk_alerts(limit=20)
    
    # Get consumption priority list
    priority_list = predictor.get_consumption_priority_list()
    
    # Get category risk summary
    category_summary = predictor.get_category_risk_summary()
    
    # Save high-risk predictions to database
    for pred in predictions:
        if pred['priority'] in ['critical', 'high']:
            WastePrediction.objects.update_or_create(
                user=request.user,
                inventory_item=pred['inventory_item'],
                item_name=pred['item_name'],
                predicted_waste_date=pred['expiration_date'],
                defaults={
                    'category': pred['category'],
                    'predicted_waste_probability': Decimal(str(pred['risk_score'])),
                    'reasoning': pred['reasoning']
                }
            )
    
    context = {
        'predictions': predictions,
        'alerts': alerts,
        'priority_list': priority_list,
        'category_summary': category_summary,
        'days_ahead': days_ahead,
        'current_season': predictor._get_current_season(),
    }
    
    return render(request, 'ai_analytics/expiration_risks.html', context)


@login_required
@require_http_methods(["GET"])
def get_expiration_alerts(request):
    """
    API endpoint for getting expiration alerts (for dashboard/widget).
    """
    predictor = ExpirationRiskPredictor(request.user)
    alerts = predictor.get_high_risk_alerts(limit=5)
    
    alerts_data = [
        {
            'type': alert['type'],
            'item_name': alert['item_name'],
            'days_until_expiry': alert['days_until_expiry'],
            'risk_score': float(alert['risk_score']),
            'recommended_action': alert['recommended_action'],
            'url': alert['url'],
        }
        for alert in alerts
    ]
    
    return JsonResponse({'alerts': alerts_data})
