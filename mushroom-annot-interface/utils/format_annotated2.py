import collections
import random
import re
import string

import Levenshtein
import numpy as np
import tqdm
from unicategories import categories

from annotation.models import *

CHARS_TO_NORMALIZE =  (
    re.compile(
        r'^[' + 
        re.escape(
            string.punctuation 
            + string.whitespace
            + ''.join(categories['P'].characters()) 
            + ''.join(categories['Z'].characters())
        ) + ']+'
    ),
    re.compile(
        r'[' + 
        re.escape(
            string.punctuation 
            + string.whitespace
            + ''.join(categories['P'].characters()) 
            + ''.join(categories['Z'].characters())
            ) + ']+$'
        ),
)


def cleanup_spans(annotation):
    """your friendly neighborhood nornmalizing function; handles the work of one annotator on a datapoint and merges and trims spans appropriately."""
    trim_step1, trim_step2 = CHARS_TO_NORMALIZE
    # step 1. : normalize string & punctuation across spans, 
    nzed_spans = []
    current_last_index = -1
    for span in annotation.json_highlighted_spans.strip().strip(';').split(';'):
        if not span.strip():
            continue
        start, end = map(int, span.split(':'))
        do_ltrim = re.search(trim_step1, annotation.datapoint.model_output[start:])
        if do_ltrim:
            start = do_ltrim.end() + start # keep track of text fragment offset
        do_rtrim = re.search(trim_step1, annotation.datapoint.model_output[end:])
        if do_rtrim:
            end = do_rtrim.end() + end # keep track of text fragment offset
        if start != end:
            # ignore dummy spans
            if start != current_last_index:
                # create new span
                nzed_spans.append((start, end))
                current_last_index = end
            else:
                # merge running spans
                nzed_spans[-1] = (nzed_spans[-1][0], end)
    # step 2. : drop trailing string & punctuation
    clean_spans = []
    for start, end in nzed_spans:
        do_rtrim = re.search(trim_step2, annotation.datapoint.model_output[start:end])
        if do_rtrim:
            end = do_rtrim.start() + start # keep track of text fragment offset
        clean_spans.append((start, end))
    return clean_spans
                

def merge_annots(annotations, bootstrap_=False, max_annotators_=3):
    """converts a bunch of annotations into a bunch of labels."""
    selected = [set() for _ in annotations]
    for idx, a in enumerate(annotations):
        for span in cleanup_spans(a):
            selected[idx] |= set(range(*span))
    if bootstrap_: 
        selected = random.sample(selected, min(len(selected), max_annotators_))
    if not any(selected):
        return []
    min_idx = min(min(slct) for slct in selected if slct)
    max_idx = max(max(slct) for slct in selected if slct)
    current_weight = -1
    spans = []
    end = -1
    in_span = False
    for idx in range(min_idx, max_idx + 2):
         new_weight = sum(1 for slct in selected if idx in slct)
         if new_weight != current_weight:
             if in_span:
                 spans[-1]['end'] = idx
             if new_weight != 0:
                 spans.append({
                    'start': idx, 
                    'prob': new_weight / len(selected),
                 })
                 in_span = True
             else:
                 in_span = False
             current_weight = new_weight
    return spans


def to_dict(datapoint, invalids=None, bootstrap_=False, max_annotators_=3):
    """from Django database object to pandas-friendly record. Don't mind the kwargs ending in _, they're here for analysis"""
    dict_rep = {
        'id': datapoint.id,
        'lang': datapoint.language,
        'model_input': datapoint.model_input,
        'model_output_text': datapoint.model_output,
        'model_id': datapoint.hf_model_name,
        'soft_labels': merge_annots(
            (
                datapoint.annotation_set.all() 
                if invalids is None else 
                datapoint.annotation_set.exclude(id__in=invalids)
            ),
            bootstrap_=bootstrap_,
            max_annotators_=max_annotators_,
        ),
    }
    hard_labels = [] 
    prev_end = -1
    for start, end in (
        (lbl['start'], lbl['end']) 
        for lbl in dict_rep['soft_labels']
        if lbl['prob'] > 0.5
    ):
        if start == prev_end:
            hard_labels[-1][-1] = end
        else:
            hard_labels.append([start, end])
        prev_end = end
    dict_rep['hard_labels'] = hard_labels
    return dict_rep
    
    
def bootstrap(k=100, invalids=None, max_annotators=3):
    for lang in ['ZH', 'EN']:
        all_scores = []
        for _ in tqdm.trange(k, leave=False):
           scores = []
           for dp in tqdm.tqdm(Datapoint.objects.filter(language=lang), leave=False):
                scores.append(compute_iou(to_dict(dp, invalids=invalids, bootstrap_=True, max_annotators_=max_annotators)['soft_labels']))
           all_scores.append(np.mean(scores))
        print(lang, np.mean(all_scores), '±', np.std(all_scores))

def compute_iou(soft_labels):
     if soft_labels == []: return 1.
     union = sum(1 * (lbl['end'] - lbl['start']) for lbl in soft_labels)
     intersection = sum(lbl['prob'] * (lbl['end'] - lbl['start']) for lbl in soft_labels)
     return intersection / union

def get_default_invalids():
    return set(
        Annotation.objects
        .filter(json_highlighted_spans='')
        .exclude(comments__icontains='no hallucination')
        .exclude(comments__icontains='correct')
        .exclude(comments__istartswith='todo bien')
        .exclude(comments__istartswith='todo correcto')
        .exclude(comments__in=['La información es respaldada por wikipedia (The Answer is supported by the information provided)'])
        .values_list('id', flat=True)
    )

def indexer(ref):
    def get_idx(row):
         subref = ref[row['lang']]
         seeks = row['model_input']
         if seeks in subref:
             print('.', end='')
             return subref[seeks]
         elif row['lang'] in ['ZH']:
             return None
         else:
             cand = sorted(subref.keys(), key=lambda k: Levenshtein.distance(seeks, k))[0]
             if row['lang'] in ['DE', 'FR', 'AR', 'HI', 'EN', 'FI']:
                 return subref[cand]
             print(f'\n{seeks}\n->\n{cand}\n OK?')
             if input().lower() == 'y':
                 return subref[cand]
             else:
                 return None
         raise RuntimeError(':(')
     
    return get_idx
