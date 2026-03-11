from django.urls import path
from .views import register, login_view, logout_view, learn_more, qr_code, my_account, survey_list, take_survey, survey_instructions, thank_you, analytics_dashboard

urlpatterns = [
    # Authentication URLs
    path('', login_view, name='login'),
    path('my-account/', my_account, name='my_account'),
    path('learn-more/', learn_more, name='learn_more'),
    path('qr-code/', qr_code, name='qr_code'),
    path('register/', register, name='register'),
    path('logout/', logout_view, name='logout'),
    
    # Survey URLs
    path('surveys/', survey_list, name='survey_list'),
    path('analytics/', analytics_dashboard, name='analytics_dashboard'),
    path('instructions/<int:survey_id>/', survey_instructions, name='survey_instructions'),
    path('take/<int:survey_id>/', take_survey, name='take_survey'),
    path('thank-you/', thank_you, name='thank_you'),
]
