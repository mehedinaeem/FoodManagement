from django.urls import path
from . import views

app_name = 'ai_analytics'

urlpatterns = [
    path('', views.ai_analytics_dashboard, name='dashboard'),
    path('patterns/', views.consumption_patterns, name='consumption_patterns'),
    path('waste/', views.waste_analysis, name='waste_analysis'),
    path('meal-optimizer/', views.meal_optimizer, name='meal_optimizer'),
    path('sdg-impact/', views.sdg_impact, name='sdg_impact'),
    path('chatbot/', views.chatbot, name='chatbot'),
    path('ocr/<int:upload_id>/', views.process_ocr, name='process_ocr'),
    path('expiration-risks/', views.expiration_risks, name='expiration_risks'),
    path('api/heatmap/', views.get_heatmap_data, name='heatmap_data'),
    path('api/alerts/', views.get_expiration_alerts, name='expiration_alerts'),
]

