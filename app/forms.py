from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import Group
from django import forms
from .models import CustomUser, Rating

ROLE_CHOICES = [
    ("student", "Student"),
    ("instructor", "Instructor"),
    ("staff", "Staff"),
    ("visitor", "Visitor"),
]


class CustomUserCreationForm(UserCreationForm):
    role = forms.ChoiceField(choices=ROLE_CHOICES, required=True)

    class Meta:
        model = CustomUser
        fields = ('first_name', 'last_name', 'username', 'email')

    def save(self, commit=True):
        user = super().save(commit=commit)
        role = self.cleaned_data.get('role')

        if commit and role:
            group, _ = Group.objects.get_or_create(name=role)
            user.groups.add(group)

        return user

class UserAccountForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ('first_name', 'last_name', 'email')
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'First Name'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Last Name'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email Address'}),
        }


class RatingForm(forms.ModelForm):
    rating = forms.ChoiceField(
        choices=[(i, str(i)) for i in range(1, 6)],
        widget=forms.RadioSelect,
        label="Rate (1-5 stars)"
    )

    class Meta:
        model = Rating
        fields = ['rating']
