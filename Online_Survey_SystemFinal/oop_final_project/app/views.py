from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.contrib.auth.forms import AuthenticationForm
from .models import Survey, Question, Rating, CustomUser
from .forms import CustomUserCreationForm, RatingForm

# Authentication views
def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('survey_list')
    else:
        form = CustomUserCreationForm()
    return render(request, 'register.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('survey_list')
    else:
        form = AuthenticationForm()
    return render(request, 'login.html', {'form': form})

def logout_view(request):
    logout(request)
    return redirect('login')

# Survey views
@login_required
def survey_list(request):
    surveys = Survey.objects.all()
    return render(request, 'survey_list.html', {'surveys': surveys})

@login_required
def multiple_surveys(request):
    surveys = Survey.objects.all()
    return render(request, 'multiple_surveys.html', {'surveys': surveys})

@login_required
def survey_instructions(request, survey_id):
    survey = get_object_or_404(Survey, id=survey_id)
    return render(request, 'survey_instructions.html', {'survey': survey})

@login_required
def take_survey(request, survey_id):
    survey = get_object_or_404(Survey, id=survey_id)
    questions = survey.questions.all()

    if request.method == 'POST':
        for question in questions:
            rating_value = request.POST.get(f'rating_{question.id}')
            if rating_value:
                Rating.objects.update_or_create(
                    user=request.user,
                    question=question,
                    defaults={'rating': int(rating_value)}
                )
        return redirect('thank_you')
    else:
        return render(request, 'take_survey.html', {'survey': survey, 'questions': questions})

@login_required
def thank_you(request):
    return render(request, 'thank_you.html')