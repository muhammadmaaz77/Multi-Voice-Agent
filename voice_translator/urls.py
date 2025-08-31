from django.urls import path
from . import views

app_name = 'voice_translator'

urlpatterns = [
    path('languages/', views.LanguageListView.as_view(), name='language-list'),
    path('health/', views.health_check, name='health-check'),
    path('test-translate/', views.test_translation, name='test-translate'),
]
