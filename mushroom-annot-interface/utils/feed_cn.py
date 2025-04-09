# copy paste this into a django shell

import transformers
import pandas as pd
from annotation.models import Datapoint

df = pd.read_json('../data/chinese/chinese-for-annotation.jsonl', lines=True)
def is_ok(row):
	tokenizer = transformers.AutoTokenizer.from_pretrained(row['model_id'], token='<your_HF_token>', trust_remote_code=True)
	text = row['output_text']
	try:
		return not any(start == end for start,end in  tokenizer(text, return_offsets_mapping=True, add_special_tokens=False)['offset_mapping'])
	except:
		pieces = tokenizer.tokenize(text)
		if len(tokenizer(text, add_special_tokens=False).input_ids) != len(pieces):
			return False
		start = 0
		end = -1
		offsets = []
		for piece in tokenizer.tokenize(text):
			end = start + len(piece)
			offsets.append((start, end))
			start = end
		return end == len(text)

df['usable'] = df.apply(is_ok, axis=1)
print(df.groupby('model_id')['usable'].mean())

df = df[df.usable]

def create_datapoint(row):
	return Datapoint.objects.create(
		model_output=row['output_text'],
		model_input=row['input_question'],
		hf_model_name=row['model_id'],
		wikipedia_url=row['wiki_url'],
		language='ZH',
	)

df.apply(create_datapoint, axis=1)
