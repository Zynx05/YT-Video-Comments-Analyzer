from django.urls import path
from . import views

urlpatterns = [
    path('', views.analyze_comments, name='analyze_comments'),
    path('analyze-youtube/', views.analyze_youtube, name='analyze_youtube'),
    path('dashboard/', views.dashboard, name='dashboard'),
]