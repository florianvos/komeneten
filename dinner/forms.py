from django import forms
from .models import MenuTeaser, Score

SCORE_CHOICES = [('', '--- Kies ---')] + [(i, f'{i} / 10') for i in range(1, 11)]


class MenuTeaserForm(forms.ModelForm):
    class Meta:
        model = MenuTeaser
        fields = ['starter_hint', 'main_hint', 'dessert_hint']
        labels = {
            'starter_hint': 'Voorgerecht',
            'main_hint': 'Hoofdgerecht',
            'dessert_hint': 'Dessert',
        }
        widgets = {
            'starter_hint': forms.Textarea(attrs={
                'rows': 3, 'class': 'form-control',
                'placeholder': 'Geef een cryptische hint over het voorgerecht...',
            }),
            'main_hint': forms.Textarea(attrs={
                'rows': 3, 'class': 'form-control',
                'placeholder': 'Geef een cryptische hint over het hoofdgerecht...',
            }),
            'dessert_hint': forms.Textarea(attrs={
                'rows': 3, 'class': 'form-control',
                'placeholder': 'Geef een cryptische hint over het dessert...',
            }),
        }


class ScoreForm(forms.ModelForm):
    class Meta:
        model = Score
        fields = ['food_score', 'atmosphere_score', 'decoration_score']
        labels = {
            'food_score': 'Het eten',
            'atmosphere_score': 'Sfeer en gezelligheid',
            'decoration_score': 'De inkleding',
        }
        widgets = {
            'food_score': forms.Select(choices=SCORE_CHOICES, attrs={'class': 'form-select'}),
            'atmosphere_score': forms.Select(choices=SCORE_CHOICES, attrs={'class': 'form-select'}),
            'decoration_score': forms.Select(choices=SCORE_CHOICES, attrs={'class': 'form-select'}),
        }
