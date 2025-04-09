import datetime
import json
import pandas as pd

from django.conf import settings
from django.db.models import Max, F

from . import models
from . import scorer

def can_submit():
    return datetime.datetime.now() < settings.TEST_PHASE_END_DATE

def get_profile(user):
    profile = (
        models
        .Profile
        .objects
        .get(participant__username=user.username)
    )
    return profile

def get_rankings(_force_val=False):
    if can_submit():
        return None
        
    split = 'VAL' if _force_val else 'TST'
    submissions = models.Submission.objects.filter(split=split).values(
        'submitter__team_name', 
        'language',
        'avg_iou_score',
        'avg_cor_score',
    )
    df_rankings = pd.DataFrame.from_records(submissions)
    groupings = ['submitter__team_name', 'language']
    best_subs = df_rankings.groupby(groupings)['avg_iou_score'].max().reset_index()
    df_rankings = df_rankings.merge(best_subs)
    df_rankings = df_rankings.sort_values(by=['avg_iou_score', 'avg_cor_score'], ascending=False)
    df_rankings = df_rankings.drop_duplicates(groupings)
    return df_rankings

def get_ref_dicts(split, lang):
    refs = (
        models
        .ReferenceDataPoint
        .objects
        .filter(language=lang, split=split)
        .order_by('datapoint_id')
    )
    refs = [
        {
            'id': inst.datapoint_id,
            'soft_labels': json.loads(inst.soft_labels_json),
            'hard_labels': json.loads(inst.hard_labels_json),
            'text_len': inst.text_len,
        }
        for inst in refs
    ]
    return refs

def handle_valid_file(pred_dicts, form_dict, profile):
    split, lang, _ = pred_dicts[0]['id'].split('-')
    split, lang = split.upper(), lang.upper()
    ref_dicts = get_ref_dicts(split, lang)
    ious, cors = scorer.main(ref_dicts, pred_dicts, None)
    
    submission_inst = models.Submission.objects.create(
        identifier=form_dict['identifier'],
        language=lang,
        split=split,
        submitter=profile,
        is_prompt=form_dict['is_prompt'],
        is_rag=form_dict['is_rag'],
        system_description=form_dict['system_description'],
        dataset_description=form_dict['dataset_description'],
        plms_description=form_dict['plms_description'],
        extra_description=form_dict['extra_description'],
        avg_iou_score=ious.mean(),
        avg_cor_score=cors.mean(),
    )
    models.DataPoint.objects.bulk_create([
        models.DataPoint(
            submission=submission_inst,
            datapoint_id=pred_dict['id'],
            soft_labels_json=json.dumps(pred_dict['soft_labels']),
            hard_labels_json=json.dumps(pred_dict['hard_labels']),
            iou_score=iou_score,
            cor_score=cor_score,
        )
        for pred_dict, iou_score, cor_score in zip(pred_dicts, ious, cors)
    ])
