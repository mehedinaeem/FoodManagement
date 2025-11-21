from django.urls import path
from . import views

app_name = 'uploads'

urlpatterns = [
    path('', views.upload_list, name='list'),
    path('create/', views.upload_create, name='create'),
    path('<int:pk>/', views.upload_detail, name='detail'),
    path('<int:pk>/delete/', views.upload_delete, name='delete'),
]

