from django.urls import path
from .views import register, login_view, logout_view, survey_list, take_survey, survey_instructions, thank_you

urlpatterns = [
    # Authentication URLs
    path('', login_view, name='login'),
    path('register/', register, name='register'),
    path('logout/', logout_view, name='logout'),
    
    # Survey URLs
    path('surveys/', survey_list, name='survey_list'),
    path('instructions/<int:survey_id>/', survey_instructions, name='survey_instructions'),
    path('take/<int:survey_id>/', take_survey, name='take_survey'),
    path('thank-you/', thank_you, name='thank_you'),
]
