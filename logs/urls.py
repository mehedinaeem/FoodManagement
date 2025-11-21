from django.urls import path
from . import views

app_name = 'logs'

urlpatterns = [
    path('', views.log_list, name='list'),
    path('create/', views.log_create, name='create'),
    path('<int:pk>/', views.log_detail, name='detail'),
    path('<int:pk>/edit/', views.log_edit, name='edit'),
    path('<int:pk>/delete/', views.log_delete, name='delete'),
    path('history/', views.log_history, name='history'),
]

