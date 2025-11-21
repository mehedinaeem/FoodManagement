from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q
from .models import Resource
from .forms import ResourceFilterForm
from .tracking import TrackingAnalyzer


@login_required
def resource_list(request):
    """
    Display list of resources with filtering options.
    Shows personalized recommendations based on user's entered items when filters are applied.
    """
    resources = Resource.objects.all()
    filter_form = ResourceFilterForm(request.GET)
    
    # Get selected filters
    selected_category = None
    selected_type = None
    
    # Apply filters
    if filter_form.is_valid():
        category = filter_form.cleaned_data.get('category')
        resource_type = filter_form.cleaned_data.get('resource_type')
        search = filter_form.cleaned_data.get('search')
        
        selected_category = category
        selected_type = resource_type
        
        if category:
            resources = resources.filter(category=category)
        if resource_type:
            resources = resources.filter(resource_type=resource_type)
        if search:
            resources = resources.filter(
                Q(title__icontains=search) |
                Q(description__icontains=search)
            )
    
    # Get personalized recommendations based on user's entered items
    # Only show recommendations when a filter is selected
    personalized_recommendations = []
    if selected_category or selected_type:
        analyzer = TrackingAnalyzer(request.user)
        personalized_recommendations = analyzer.get_recommendations(
            limit=5,
            resource_category_filter=selected_category,
            resource_type_filter=selected_type
        )
    
    # Get featured resources
    featured_resources = resources.filter(featured=True)[:3]
    
    # Statistics
    total_resources = resources.count()
    
    # Category breakdown
    category_stats = resources.values('category').annotate(
        count=Count('id')
    ).order_by('-count')
    
    # Type breakdown
    type_stats = resources.values('resource_type').annotate(
        count=Count('id')
    ).order_by('-count')
    
    # Group by category for better display
    resources_by_category = {}
    for resource in resources:
        category_name = resource.get_category_display()
        if category_name not in resources_by_category:
            resources_by_category[category_name] = []
        resources_by_category[category_name].append(resource)
    
    context = {
        'resources': resources,
        'featured_resources': featured_resources,
        'filter_form': filter_form,
        'total_resources': total_resources,
        'category_stats': category_stats,
        'type_stats': type_stats,
        'resources_by_category': resources_by_category,
        'personalized_recommendations': personalized_recommendations,
        'has_filter': bool(selected_category or selected_type),
    }
    
    return render(request, 'resources/list.html', context)


@login_required
def resource_detail(request, pk):
    """
    View details of a resource.
    """
    resource = get_object_or_404(Resource, pk=pk)
    
    # Get related resources in the same category
    related_resources = Resource.objects.filter(
        category=resource.category
    ).exclude(pk=resource.pk)[:5]
    
    context = {
        'resource': resource,
        'related_resources': related_resources,
    }
    
    return render(request, 'resources/detail.html', context)


@login_required
def tracking_view(request):
    """
    Display tracking analysis with summaries and recommendations.
    """
    analyzer = TrackingAnalyzer(request.user)
    
    # Get summary
    summary = analyzer.get_summary()
    
    # Get recommendations
    recommendations = analyzer.get_recommendations(limit=6)
    
    # Get insights
    insights = analyzer.get_insights()
    
    context = {
        'summary': summary,
        'recommendations': recommendations,
        'insights': insights,
    }
    
    return render(request, 'resources/tracking.html', context)
