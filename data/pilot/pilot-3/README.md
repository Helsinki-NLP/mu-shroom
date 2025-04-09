# How to use this

1. you can restore the pilot exercise state by picking the empty database, and copying it to the DB path mentionned in the annotation interface's `settings.py`. Running `python3 manage.py runserver` afterwards will allow you to run the interface and check it out.
2. you can inspect the annotations collected by copying the full database to the same location, and running `python3 manage.py shell` to open an interactivde python shell. Here's an example of commands to feed to the shell in order to compute average IoUs:

```python
from annotation import models
import numpy as np
import pandas as pd

def read_annot(annot):
	total_length = len(annot.datapoint.model_output)
	datapoint_id = annot.datapoint_id
	username = annot.annotator.annotator.username
	selected_chars = set()
	for start, end in map(lambda span: map(int, span.split(':')), annot.json_highlighted_spans.split(';')):
		selected_chars = selected_chars | set(range(start, end))
	return {'length': total_length, 'annotator': username, 'datapoint': datapoint_id, 'selected': selected_chars}

df = pd.DataFrame.from_records([read_annot(annot) for annot in models.Annotation.objects.all()])

def merge_selections(datapoint):
	subset = df[df.datapoint == datapoint]
	intersection_, union_ = None, set()
	for selection in subset.selected:
		selection = set(selection)
		union_ = union_ | selection
		if intersection_ is None:
			intersection_ = selection
		else:
			intersection_ = intersection_ & selection
	return len(intersection_) / len(union_)


for datapoint in df.datapoint.unique():
	print(datapoint, merge_selections(datapoint))

shared = np.array([merge_selections(datapoint) for datapoint in df.datapoint.unique()])
print('Average IoU:', shared.mean(), '+-', shared.std())

```
