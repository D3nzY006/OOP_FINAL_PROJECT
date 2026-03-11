import re
from collections import Counter

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.contrib.auth.forms import AuthenticationForm
from django.db.models import Avg, Count, Sum
from django.urls import reverse
from .models import Survey, Question, Rating, CustomUser, OpenResponse
from .forms import CustomUserCreationForm, RatingForm

DEFAULT_SURVEY_QUESTIONS = [
    "The survey instructions were clear and easy to follow.",
    "The survey layout made it easy to answer questions.",
    "The questions were relevant to the survey topic.",
    "The answer choices were appropriate for each question.",
    "The survey length was reasonable.",
    "The survey interface worked smoothly on my device.",
    "I felt comfortable sharing my honest feedback.",
    "The survey helped me express my opinion effectively.",
    "The wording of each question was easy to understand.",
    "I would recommend this survey format to others.",
    "The pacing of the survey was appropriate.",
    "The design of the survey was visually clear.",
    "The response options captured my true opinion.",
    "The survey experience was engaging from start to finish.",
    "Overall, this survey was effective in collecting feedback.",
]

RATING_CHOICES = [
    (1, "Not at all Effective"),
    (2, "Slightly Effective"),
    (3, "Moderately Effective"),
    (4, "Very Effective"),
    (5, "Extremely Effective"),
]

STOP_WORDS = {
    "about", "after", "again", "also", "and", "because", "been", "being", "between",
    "both", "can", "could", "did", "does", "doing", "each", "from", "have", "having",
    "here", "into", "just", "more", "most", "much", "must", "not", "only", "other",
    "our", "out", "should", "some", "such", "than", "that", "the", "their", "them",
    "then", "there", "these", "they", "this", "those", "through", "very", "want",
    "were", "what", "when", "where", "which", "while", "who", "will", "with", "your",
}


def ensure_survey_has_15_questions(survey):
    question_count = survey.questions.count()
    if question_count >= 15:
        return

    missing_count = 15 - question_count
    start_index = question_count
    new_questions = []

    for index in range(start_index, start_index + missing_count):
        new_questions.append(
            Question(
                survey=survey,
                text=DEFAULT_SURVEY_QUESTIONS[index],
            )
        )

    Question.objects.bulk_create(new_questions)


def get_respondent_role(user):
    group_names = {group.name.lower() for group in user.groups.all()}
    if user.is_staff or user.is_superuser or "staff" in group_names:
        return "staff"
    if "instructor" in group_names:
        return "instructor"
    if "student" in group_names:
        return "student"
    if "visitor" in group_names:
        return "visitor"
    return "visitor"


def extract_top_keywords(open_responses, limit=10):
    combined_text = " ".join(
        response.response.strip().lower()
        for response in open_responses
        if response.response and response.response.strip()
    )

    words = re.findall(r"[a-zA-Z]{4,}", combined_text)
    filtered_words = [word for word in words if word not in STOP_WORDS]
    return Counter(filtered_words).most_common(limit)

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

def learn_more(request):
    return render(request, 'learn_more.html')

def qr_code(request):
    qr_target_url = request.build_absolute_uri(reverse('survey_list'))
    return render(
        request,
        'qr_code.html',
        {
            'qr_target_url': qr_target_url,
        },
    )

def my_account(request):
    account = None

    if request.user.is_authenticated:
        first_name = request.user.first_name or ""
        last_name = request.user.last_name or ""
        username = request.user.username or ""
        display_name = f"{first_name} {last_name}".strip() or username
        initials = (f"{first_name[:1]}{last_name[:1]}".strip() or username[:2]).upper()

        account = {
            'first_name': first_name,
            'last_name': last_name,
            'username': username,
            'email': request.user.email,
            'role': get_respondent_role(request.user).title(),
            'display_name': display_name,
            'initials': initials,
        }

    return render(request, 'my_account.html', {'account': account})

# Survey views
@login_required
def survey_list(request):
    surveys = Survey.objects.all()
    return render(request, 'survey_list.html', {'surveys': surveys})


def analytics_dashboard(request):
    ratings = Rating.objects.select_related('question__survey', 'user')
    open_responses = OpenResponse.objects.select_related('survey', 'user')

    total_ratings = ratings.count()
    total_responses = open_responses.count()
    average_rating = ratings.aggregate(avg=Avg('rating'))['avg'] or 0
    positive_count = ratings.filter(rating__gte=4).count()
    satisfaction_rate = (positive_count / total_ratings * 100) if total_ratings else 0

    expected_total_ratings = (
        open_responses
        .annotate(question_total=Count('survey__questions', distinct=True))
        .aggregate(total=Sum('question_total'))['total'] or 0
    )
    completion_rate = (total_ratings / expected_total_ratings * 100) if expected_total_ratings else 0
    completion_rate = min(completion_rate, 100)

    respondent_user_ids = set(open_responses.values_list('user_id', flat=True))
    respondent_user_ids.update(ratings.values_list('user_id', flat=True))
    respondents = (
        CustomUser.objects
        .filter(id__in=respondent_user_ids)
        .prefetch_related('groups')
    )

    role_counts = {
        'student': 0,
        'instructor': 0,
        'staff': 0,
        'visitor': 0,
    }
    for user in respondents:
        role = get_respondent_role(user)
        role_counts[role] += 1

    rating_buckets = {score: 0 for score in range(1, 6)}
    for row in ratings.values('rating').annotate(count=Count('id')):
        rating_buckets[row['rating']] = row['count']

    rating_breakdown = []
    for score in range(5, 0, -1):
        count = rating_buckets[score]
        percent = (count / total_ratings * 100) if total_ratings else 0
        rating_breakdown.append({
            'label': f'{score} Star',
            'count': count,
            'percent': percent,
        })

    responses_by_survey = list(
        open_responses
        .values('survey__title')
        .annotate(count=Count('id'))
        .order_by('-count', 'survey__title')
    )
    max_response_count = responses_by_survey[0]['count'] if responses_by_survey else 0
    for row in responses_by_survey:
        row['width_percent'] = (row['count'] / max_response_count * 100) if max_response_count else 0

    avg_rating_by_survey = list(
        ratings
        .values('question__survey__title')
        .annotate(avg=Avg('rating'), count=Count('id'))
        .order_by('-avg', 'question__survey__title')
    )
    for row in avg_rating_by_survey:
        row['width_percent'] = (row['avg'] / 5 * 100) if row['avg'] else 0

    top_keywords = extract_top_keywords(open_responses, limit=12)
    max_keyword_count = top_keywords[0][1] if top_keywords else 0
    keyword_rows = []
    for keyword, count in top_keywords:
        keyword_rows.append({
            'keyword': keyword,
            'count': count,
            'size': (count / max_keyword_count * 100) if max_keyword_count else 0,
        })

    context = {
        'total_responses': total_responses,
        'total_respondents': len(respondent_user_ids),
        'average_rating': average_rating,
        'completion_rate': completion_rate,
        'satisfaction_rate': satisfaction_rate,
        'rating_breakdown': rating_breakdown,
        'responses_by_survey': responses_by_survey[:8],
        'avg_rating_by_survey': avg_rating_by_survey[:8],
        'role_counts': role_counts,
        'keyword_rows': keyword_rows,
    }
    return render(request, 'analytics.html', context)

# @login_required
# def multiple_surveys(request):
#     surveys = Survey.objects.all()
#     return render(request, 'multiple_surveys.html', {'surveys': surveys})

@login_required
def survey_instructions(request, survey_id):
    survey = get_object_or_404(Survey, id=survey_id)
    return render(request, 'survey_instructions.html', {'survey': survey})

@login_required
def take_survey(request, survey_id):
    survey = get_object_or_404(Survey, id=survey_id)
    ensure_survey_has_15_questions(survey)
    questions = survey.questions.order_by('id')[:15]

    if request.method == 'POST':
        for question in questions:
            rating_value = request.POST.get(f'rating_{question.id}')
            if rating_value:
                Rating.objects.update_or_create(
                    user=request.user,
                    question=question,
                    defaults={'rating': int(rating_value)}
                )

        open_response_text = request.POST.get('open_response', '').strip()
        OpenResponse.objects.update_or_create(
            user=request.user,
            survey=survey,
            defaults={'response': open_response_text}
        )
        return redirect('thank_you')

    open_response = OpenResponse.objects.filter(
        user=request.user,
        survey=survey
    ).values_list('response', flat=True).first() or ''

    return render(
        request,
        'take_survey.html',
        {
            'survey': survey,
            'questions': questions,
            'rating_choices': RATING_CHOICES,
            'open_response': open_response,
        }
    )

@login_required
def thank_you(request):
    return render(request, 'thank_you.html')
