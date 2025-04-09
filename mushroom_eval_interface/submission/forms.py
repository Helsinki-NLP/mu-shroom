from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth import forms as auth_forms
from django.core.exceptions import ValidationError

from datetime import datetime

from . import models, services, scorer


class UserAndPreferencesCreationForm(auth_forms.UserCreationForm):
    team_name = forms.CharField()

    class Meta:
        fields = ("username", "email", "password1", "password2", "team_name")
        model = get_user_model()

    def save(self, *args, **kwargs):
        # Let the UserCreationForm handle the user creation
        user = super().save(*args, **kwargs)
        # With the user create a Member
        models.Profile.objects.create(participant=user, team_name=self.cleaned_data.get("team_name"))
        return user


class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True


def _check_aligned(pdict, rdict, fname):
    if pdict['id'] != rdict['id']:
        raise ValidationError(f'IDs are not correctly aligned in {fname}: {pdict["id"]} != {rdict["id"]}')
    if 'hard_labels' in pdict:
        for start, end in pdict['hard_labels']:
            if not (0 <= start < end <= rdict['text_len']):
                 raise ValidationError(
                     f'hard prediction {pdict["id"]} concerns chars not in range (or ends before it starts):\n'
                     f'you should have 0 <= pred start ({start}) < pred end ({end}) <= pred max {rdict["text_len"]}'
                 )
    if 'soft_labels' in pdict:
        for lbl in pdict['soft_labels']:
            start, end = lbl['start'], lbl['end']
            if not (0 <= start < end <= rdict['text_len']):
                 raise ValidationError(
                     f'soft prediction {pdict["id"]} concerns chars not in range  (or ends before it starts):\n'
                     f'you should have 0 <= pred start ({start}) < pred end ({end}) <= pred max {rdict["text_len"]}'
                 )


class MultipleFileField(forms.FileField):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("widget", MultipleFileInput())
        super().__init__(*args, **kwargs)

    def clean(self, data, initial=None):
        single_file_clean = super().clean
        if isinstance(data, (list, tuple)):
            result = [single_file_clean(d, initial) for d in data]
        else:
            result = [single_file_clean(data, initial)]
        results_ = []
        seen_langs, seen_split = set(), set()
        for fname in result:
            if not fname.name.endswith('.jsonl'):
                raise ValidationError(f'All files should be in the .jsonl format, but you submitted {fname.name}.')
            try:
                pred_dicts = scorer.load_jsonl_file_to_records(fname, is_ref=False)
                pred_dicts = [
                    {
                        key: pdict[key] 
                        for key in ['id', 'soft_labels', 'hard_labels'] 
                        if key in pdict
                    } 
                    for pdict in pred_dicts
                ]
            except Exception as e:
                 raise ValidationError(f"Couldn't parse {fname.name}: {e}")
            split, lang, _ = pred_dicts[0]['id'].split('-')
            split, lang = split.upper(), lang.upper()
            if split == 'TST':
                if settings.TEST_PHASE_START_DATE > datetime.now():
                    raise ValidationError(f"Evaluation phase hasn't started yet, but {fname.name} is a test set prediction.")
            ref_dicts = services.get_ref_dicts(split, lang)
            for pdict, rdict in zip(pred_dicts, ref_dicts):
                _check_aligned(pdict, rdict, fname.name)
            # if not all(pdict['id'] == rdict['id'] for pdict, rdict in zip(pred_dicts, ref_dicts)):
            #    raise ValidationError(f'IDs are not correctly aligned in {fname.name}')
            seen_split.add(split)
            if lang in seen_langs:
                raise ValidationError(f'Multiple files for language {lang}')
            seen_langs.add(lang)
            results_.append(pred_dicts)
        if len(seen_split) != 1:
            raise ValidationError(f'The files should all correspond to the same split (got {seen_split})')
        return results_


class SubmissionUploadForm(forms.Form):
    identifier = forms.CharField(label="Provide an identifier for this submission:", max_length=50, required=True)
    system_description = forms.CharField(label="How does the system for this submission work?", max_length=400, required=True, widget=forms.widgets.Textarea)
    is_prompt = forms.ChoiceField(label="Did your submission use prompts?", required=True, widget=forms.RadioSelect, choices={True:'yes', False:'no'})
    is_rag = forms.ChoiceField(label="Did your submission use RAG?", required=True, widget=forms.RadioSelect, choices={True:'yes', False:'no'})
    dataset_description = forms.CharField(label="What datasets did you use in your submission?", max_length=400, required=True, widget=forms.widgets.Textarea)
    plms_description = forms.CharField(label="What (pretrained) models did you use in your submission?", max_length=400, required=True, widget=forms.widgets.Textarea)
    extra_description = forms.CharField(label="Any additional information on your system description?", max_length=400, required=False, widget=forms.widgets.Textarea)
    files = MultipleFileField(label='upload your JSONL prediction files here:')


class SubmissionMetadataForm(forms.ModelForm):
    class Meta:
        model = models.Submission
        fields = ["identifier", 'system_description', 'is_prompt', 'is_rag', 'dataset_description', 'plms_description', 'extra_description']
        labels = {
            "identifier": 'Provide an identifier for this submission:',
            'system_description': "How does the system for this submission work?",
            'is_prompt': "Did your submission use prompts?",
            'is_rag': "Did your submission use RAG?",
            'dataset_description': "What datasets did you use in your submission?",
            'plms_description': "What (pretrained) models did you use in your submission?",
            'extra_description': "Any additional information on your system description?",
        }
        widgets = {
            'is_prompt': forms.RadioSelect(choices={True:'yes', False:'no'}),
            'is_rag': forms.RadioSelect(choices={True:'yes', False:'no'}),
        }

