from django.db import models
from django.contrib.auth import models as auth_models
from django.utils.translation import gettext_lazy as _


class Profile(models.Model):
    participant = models.OneToOneField(auth_models.User, on_delete=models.CASCADE)
    team_name = models.CharField(max_length=200)


class Language(models.TextChoices):
    AR = 'AR', _('Arabic')
    CA = 'CA', _('Catalan')
    CS = 'CS', _('Czech')
    DE = 'DE', _('German')
    EN = 'EN', _('English')
    ES = 'ES', _('Spanish')
    EU = 'EU', _('Basque')
    FA = 'FA', _('Farsi')
    FI = 'FI', _('Finnish')
    FR = 'FR', _('French')
    HI = 'HI', _('Hindi')
    IT = 'IT', _('Italian')
    SV = 'SV', _('Swedish')
    ZH = 'ZH', _('Chinese')


class DataSplit(models.TextChoices):
    val = 'VAL', _('Val')
    test = 'TST', _('Test')

class Submission(models.Model):
    identifier = models.CharField(max_length=50)
    system_description = models.TextField()
    is_prompt = models.BooleanField()
    is_rag = models.BooleanField()
    dataset_description = models.TextField()
    plms_description = models.TextField()
    extra_description = models.TextField()
    submitter = models.ForeignKey(Profile, on_delete=models.CASCADE)
    language = models.CharField(max_length=2, choices=Language.choices)
    split = models.CharField(max_length=3, choices=DataSplit.choices)
    avg_iou_score = models.FloatField()
    avg_cor_score = models.FloatField()


class DataPoint(models.Model):
    submission = models.ForeignKey(Submission, on_delete=models.CASCADE)
    datapoint_id = models.CharField(max_length=20)
    soft_labels_json = models.TextField()
    hard_labels_json = models.TextField()
    iou_score = models.FloatField()
    cor_score = models.FloatField()
    extra_analysis_json = models.TextField()

class ReferenceDataPoint(models.Model):
    language = models.CharField(max_length=2, choices=Language.choices)
    split = models.CharField(max_length=3, choices=DataSplit.choices)
    datapoint_id = models.CharField(max_length=20)
    soft_labels_json = models.TextField()
    hard_labels_json = models.TextField()
    text_len = models.IntegerField()

