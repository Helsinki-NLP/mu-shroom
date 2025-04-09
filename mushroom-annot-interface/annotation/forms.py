from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth import forms as auth_forms
from . import models

class UserAndPreferencesCreationForm(auth_forms.UserCreationForm):
    language = forms.ChoiceField(choices=models.Language.choices)
    
    class Meta:
        fields = ("username", "email", "password1", "password2", "language")
        model = get_user_model()
    
    def save(self, *args, **kwargs):
        # Let the UserCreationForm handle the user creation
        user = super().save(*args, **kwargs)
        # With the user create a Member
        models.Profile.objects.create(annotator=user, language=self.cleaned_data.get("language"))
        return user

