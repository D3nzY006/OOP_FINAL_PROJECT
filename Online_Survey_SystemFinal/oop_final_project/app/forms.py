from django.contrib.auth.forms import UserCreationForm
from django import forms
from .models import CustomUser, Rating

class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = CustomUser
        fields = ('username', 'email')

class RatingForm(forms.ModelForm):
    rating = forms.ChoiceField(
        choices=[(i, str(i)) for i in range(1, 6)],
        widget=forms.RadioSelect,
        label="Rate (1-5 stars)"
    )

    class Meta:
        model = Rating
        fields = ['rating']