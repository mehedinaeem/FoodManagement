from django.urls import path
from . import views

app_name = 'inventory'

urlpatterns = [
    # User inventory management
    path('', views.inventory_list, name='list'),
    path('create/', views.inventory_create, name='create'),
    path('<int:pk>/', views.inventory_detail, name='detail'),
    path('<int:pk>/edit/', views.inventory_edit, name='edit'),
    path('<int:pk>/delete/', views.inventory_delete, name='delete'),
    path('<int:pk>/mark-consumed/', views.inventory_mark_consumed, name='mark_consumed'),
    # Food items reference database
    path('food-items/', views.food_items_list, name='food_items_list'),
    path('food-items/<int:pk>/', views.food_item_detail, name='food_item_detail'),
]

