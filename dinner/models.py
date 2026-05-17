from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator


class Couple(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='couple')
    name = models.CharField(max_length=100)

    @property
    def photo(self):
        return f"{self.user.username}.jpg"

    def __str__(self):
        return self.name


class DinnerDate(models.Model):
    host = models.ForeignKey(Couple, on_delete=models.CASCADE, related_name='hosted_dinners')
    date = models.DateField(unique=True)

    class Meta:
        ordering = ['date']

    def __str__(self):
        return f"{self.host.name} — {self.date.strftime('%d %B %Y')}"

    def is_past(self):
        from datetime import date
        return self.date < date.today()


class MenuTeaser(models.Model):
    dinner_date = models.OneToOneField(DinnerDate, on_delete=models.CASCADE, related_name='teaser')
    text = models.TextField(blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Teaser voor {self.dinner_date}"


class Invitation(models.Model):
    couple = models.OneToOneField(Couple, on_delete=models.CASCADE, related_name='invitation')
    text = models.TextField(blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Uitnodiging van {self.couple.name}"


class Availability(models.Model):
    couple = models.ForeignKey(Couple, on_delete=models.CASCADE, related_name='availabilities')
    date = models.DateField()

    class Meta:
        unique_together = ('couple', 'date')
        ordering = ['date']

    def __str__(self):
        return f"{self.couple.name} beschikbaar op {self.date}"


class Score(models.Model):
    dinner_date = models.ForeignKey(DinnerDate, on_delete=models.CASCADE, related_name='scores')
    scorer = models.ForeignKey(Couple, on_delete=models.CASCADE, related_name='given_scores')
    food_score = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(10)])
    atmosphere_score = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(10)])
    decoration_score = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(10)])
    submitted_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('dinner_date', 'scorer')

    def __str__(self):
        return f"Score door {self.scorer.name} voor {self.dinner_date}"

    def total(self):
        return self.food_score + self.atmosphere_score + self.decoration_score
