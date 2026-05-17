from django import forms
from .models import Invitation, MenuTeaser, Score

SCORE_CHOICES = [('', '--- Kies ---')] + [(i, f'{i} / 10') for i in range(1, 11)]


class InvitationForm(forms.ModelForm):
    class Meta:
        model = Invitation
        fields = ['text']
        labels = {'text': 'Jullie uitnodiging'}
        widgets = {
            'text': forms.Textarea(attrs={
                'rows': 6,
                'class': 'form-control',
                'placeholder': 'Schrijf hier jullie originele uitnodiging...',
                'style': 'font-family:Georgia,serif;font-size:1rem;',
            }),
        }


class MenuTeaserForm(forms.ModelForm):
    class Meta:
        model = MenuTeaser
        fields = ['text']
        labels = {'text': 'Menu'}
        widgets = {
            'text': forms.Textarea(attrs={
                'rows': 6, 'class': 'form-control',
                'placeholder': 'Beschrijf jullie menu...',
                'style': 'font-family:Georgia,serif;font-size:1rem;',
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
