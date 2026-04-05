from django.contrib.auth.models import AbstractUser
from django.db import models

class CustomUser(AbstractUser):
    pass

class Survey(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.title

    def get_icon(self):
        title_lower = self.title.lower() if self.title else ''
        if 'student' in title_lower:
            return ('🎓', '36px')
        elif 'instructor' in title_lower:
            return ('🏫', '36px')
        elif 'staff' in title_lower:
            return ('💼', '36px')
        elif 'visitor' in title_lower:
            return ('👥', '36px')
        elif 'general' in title_lower:
            return ('🌍', '36px')
        return ('📋', '36px')

class Question(models.Model):
    survey = models.ForeignKey(Survey, on_delete=models.CASCADE, related_name='questions')
    text = models.CharField(max_length=300)

    def __str__(self):
        return self.text

class Rating(models.Model):
    user = models.ForeignKey('CustomUser', on_delete=models.CASCADE)
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    rating = models.IntegerField(choices=[(i, i) for i in range(1, 6)])
    created_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ('user', 'question')

    def __str__(self):
        return f"{self.user.username} - {self.question.text} - {self.rating} stars"


class OpenResponse(models.Model):
    user = models.ForeignKey('CustomUser', on_delete=models.CASCADE)
    survey = models.ForeignKey(Survey, on_delete=models.CASCADE, related_name='open_responses')
    response = models.TextField(blank=True)
    created_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ('user', 'survey')

    def __str__(self):
        return f"{self.user.username} - {self.survey.title}"
