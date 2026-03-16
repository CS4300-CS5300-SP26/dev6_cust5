from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import RoommatePost
from django import forms

class RoommatePostForm(forms.ModelForm):
    message = forms.CharField(
        widget=forms.Textarea(attrs={
            'rows': 6,
            'cols': 50,
            'style': 'width:100%;'
        })
    )
    class Meta:
        model = RoommatePost
        fields = ['message', 'date', 'status', 'rent', 'property_type']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
            'property_type': forms.Select(choices=[
                ('', 'Select type'),
                ('apartment', 'Apartment'),
                ('house', 'House'),
                ('condo', 'Condo'),
                ('townhouse', 'Townhouse'),
            ]),
        }

class CustomRegisterForm(UserCreationForm):
    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['email'].required = False  