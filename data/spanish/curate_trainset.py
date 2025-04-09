import os
import pandas as pd


def cleanjson(f, removeindices, val_questions):
    subdf = pd.read_json('outputs/'+f,lines=True)
    subdf = subdf[:50]
    assert (subdf.question[:50] == val_questions).sum() == 50
    subdf['config_info'] = f.rstrip('.jsonl')
    return subdf.drop(removeindices)
    

valpath = 'mushroom.es-val.v1.jsonl'
dfpath = 'ready_for_anotation_fixed.tsv'
trainpath = 'outputs/es-trainset.jsonl'

try:
    os.remove(trainpath)
except OSError:
    pass

val = pd.read_json(valpath, lines=True)
df = pd.read_csv(dfpath, sep='\t')

df = df[:50]
assert (df.question == val.model_input).sum() == 50

dir_path = "/home/vazquezj/git/mu-shroom/data/spanish/outputs/"
files = set([f for f in os.listdir(dir_path) if not 'annotation' in f])
take_away = {model: df[df.config_info == model].index.tolist() for model in files}

finaldfcols = ['title', 'question', 'model_id', 'config_info', 'lang', 'output_text', 'output_tokens', 'output_logits']
traindf = pd.DataFrame(columns=finaldfcols)
for file,indices in take_away.items():
    temp = cleanjson(file,indices, val.model_input)
    temp = temp[finaldfcols]
    traindf = pd.concat((traindf,temp))

traindf.to_json(trainpath, orient='records', lines=True)
# load with: train = pd.read_json(valpath, lines=True)
