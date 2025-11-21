from django.urls import path
from . import views

app_name = 'inventory'

urlpatterns = [
    path('', views.inventory_list, name='list'),
    path('create/', views.inventory_create, name='create'),
    path('<int:pk>/', views.inventory_detail, name='detail'),
    path('<int:pk>/edit/', views.inventory_edit, name='edit'),
    path('<int:pk>/delete/', views.inventory_delete, name='delete'),
    path('<int:pk>/mark-consumed/', views.inventory_mark_consumed, name='mark_consumed'),
]

