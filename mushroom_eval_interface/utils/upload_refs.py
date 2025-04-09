import pandas as pd
import json
import pathlib
from submission.models import ReferenceDataPoint

for file in pathlib.Path('../splits/val/v2/').glob('*.jsonl'):
    df = pd.read_json(file, lines=True)
    split = 'VAL'
    langs = df.lang.unique()
    assert len(langs) == 1, 'eh!?'
    lang = langs[0]
    def create_ref(row):
        return ReferenceDataPoint.objects.create(
            language=lang.upper(),
            split=split,
            datapoint_id=row['id'],
            soft_labels_json=json.dumps(row['soft_labels']),
            hard_labels_json=json.dumps(row['hard_labels']),
            text_len=len(row['model_output_text']),
        )
    df.apply(create_ref, axis=1)
