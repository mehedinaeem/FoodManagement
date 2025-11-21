from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
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
    Display waste analysis and predictions.
    """
    analyzer = AIConsumptionAnalyzer(request.user)
    waste_estimator = WasteEstimator(request.user)
    
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
    weekly_waste = waste_estimator.estimate_weekly_waste()
    monthly_waste = waste_estimator.estimate_monthly_waste()
    community_comparison = waste_estimator.compare_to_community()
    waste_projection = waste_estimator.generate_waste_projection(weeks=4)
    
    context = {
        'waste_predictions': waste_predictions,
        'weekly_waste': weekly_waste,
        'monthly_waste': monthly_waste,
        'community_comparison': community_comparison,
        'waste_projection': waste_projection,
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
        if budget_limit:
            budget_limit = float(budget_limit)
        else:
            budget_limit = None
        
        meal_plan = optimizer.optimize_weekly_meal_plan(budget_limit=budget_limit)
        
        context = {
            'meal_plan': meal_plan,
            'budget_limit': budget_limit,
        }
        
        return render(request, 'ai_analytics/meal_plan_result.html', context)
    
    # Get user's budget preference
    budget_map = {'low': 50, 'medium': 75, 'high': 100}
    profile = getattr(request.user, 'profile', None)
    budget_range = profile.budget_range if profile else 'medium'
    default_budget = budget_map.get(budget_range, 75)
    
    context = {
        'default_budget': default_budget,
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
    """
    upload = get_object_or_404(Upload, id=upload_id, user=request.user)
    processor = OCRProcessor(upload)
    
    use_google_vision = request.GET.get('use_google', 'false') == 'true'
    result = processor.extract_food_data(use_google_vision=use_google_vision)
    
    if request.method == 'POST':
        # User confirmed extraction
        if result.get('success'):
            extracted = result['extracted_data']
            # Allow user to edit before creating
            item_data = processor.create_inventory_item_from_extraction(extracted, confirm=True)
            
            # Create inventory item
            item = InventoryItem.objects.create(
                user=request.user,
                item_name=request.POST.get('item_name', item_data['item_name']),
                quantity=float(request.POST.get('quantity', item_data['quantity'])),
                unit=request.POST.get('unit', item_data['unit']),
                category=request.POST.get('category', item_data['category']),
                purchase_date=timezone.now().date(),
                expiration_date=request.POST.get('expiration_date') or item_data.get('expiration_date'),
            )
            item.update_status()
            
            # Associate upload
            upload.associated_inventory = item
            upload.save()
            
            return redirect('inventory:detail', pk=item.id)
    
    context = {
        'upload': upload,
        'result': result,
        'extracted_data': result.get('extracted_data', {}),
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
