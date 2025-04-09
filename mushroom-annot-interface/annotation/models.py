from django.db import models
from django.contrib.auth import models as auth_models
from django.utils.translation import gettext_lazy as _

class Language(models.TextChoices):
    AR = 'AR', _('Arabic')
    CA = 'CA', _('Catalan'),
    CS = 'CS', _('Czech'),
    EU = 'EU', _('Basque'),
    DE = 'DE', _('German')
    EN = 'EN', _('English')
    ES = 'ES', _('Spanish')
    FA = 'FA', _('Farsi')
    FI = 'FI', _('Finnish')
    FR = 'FR', _('French')
    HI = 'HI', _('Hindi')
    IT = 'IT', _('Italian')
    SV = 'SV', _('Swedish')
    ZH = 'ZH', _('Chinese')

class Datapoint(models.Model):
    model_output = models.TextField()
    model_input = models.TextField()
    hf_model_name = models.CharField(max_length=200)
    language = models.CharField(max_length=2, choices=Language.choices)
    json_meta = models.TextField()
    wikipedia_url = models.TextField()

class Profile(models.Model):
    annotator = models.OneToOneField(auth_models.User, on_delete=models.CASCADE)
    language = models.CharField(max_length=2, choices=Language.choices)

class Annotation(models.Model):
    datapoint = models.ForeignKey(Datapoint, on_delete=models.CASCADE)
    annotator = models.ForeignKey(Profile, on_delete=models.CASCADE)
    json_highlighted_spans = models.TextField()
    comments = models.TextField()
