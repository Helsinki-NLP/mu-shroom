import os
import random
import json
import pathlib
import pandas as pd
import tqdm
from pudb import set_trace

TOTAL = 156  # number of items to annotate

def clean_files():
    for file in files:
        if 'annotation' in file:
            files.pop(files.index(file))

    for file in files:
        if 'pilot' in file:
            files.pop(files.index(file))
    return files

def crappyanswer(row):
    print('\n\n \tWARNING!!!! \nAll answers seem to be crap for this question \n SKIPPING...\n',row)
    row['output_text'] = ''
    row['output_tokens'] = ''
    row['output_logits'] = 0
    return row

def open_all():
    return [map(json.loads, open(dir_path + file, 'r')) for file in files]

def get_all_candidates(handlers):
    candidates = [(file, next(fh)) for file, fh in zip(files, handlers)]
    random.shuffle(candidates)
    return candidates

def fyc(answer):
    userans = None
    accepted_answers = {'y','n', 'yes', 'no'}

    print("Link:   " + answer["url-localized"])
    print("QUESTION:   " + answer["FR questions"])
    print("LLM-OUTPUT: \n\n" + answer["output_text"] + "<END_OF_LLM_OUTPUT> \n\n")

    while not userans in accepted_answers:
        userans = input("Is this output to be annotated (y/n)? ").strip().lower()
        if userans not in accepted_answers:
            print('ERROR only accepted answers are: y, n, yes, no, Y, N, YES, NO')
        printfull  = False
    return userans in {'y', 'yes'}


def main():
    selected = []
    if os.path.exists("badindices.txt"):
        with open("badindices.txt") as f:
            badindices = [int(x) for x in f.readlines()]
    else:
        badindices = []
    f_badindices = open("badindices.txt", 'a')

    outfile = 'ready_for_annotation_fr.test.tsv'
    items = {}
    if pathlib.Path(outfile).is_file():
        finalanswers = pd.read_csv(outfile, sep='\t')
        finalanswers.to_csv(outfile+'.backup', sep='\t', index=False)
        finalanswers = finalanswers.drop_duplicates(['title', 'Primary Wikipedia URL'])
        items = set(finalanswers.title.unique())
        selected = finalanswers.to_dict(orient='records')
        print(f'INFO: Found started file: {outfile}.')

    qnum = len(selected)
    i = qnum
    print(f'INFO: Starting from question number {qnum+1}\n')
    file_handlers = open_all()
    with tqdm.trange(qnum, TOTAL, desc='remaining') as pbar:
      while i < TOTAL:
        answers_candidates = get_all_candidates(file_handlers)
        url_idx = int(answers_candidates[0][1]["URL-idx"])
        if answers_candidates[0][1]['title'] in items or url_idx in badindices:
            continue
        assert len({cd[1]['title'] for cd in answers_candidates}) == 1
        set_trace()
        items.add(answers_candidates[0][1]['title'])
        i += 1
        
        selected_candidate, chosenf = None, None
        for fname, candidate in answers_candidates:
            if selected_candidate is None and fyc(candidate):
                selected_candidate = candidate
                chosenf = fname
        if selected_candidate is None:
            badindices.append(url_idx)
            f_badindices.write(str(i) +"\n")
            continue

        selected_candidate['url-localized'] = selected_candidate['url-localized']
        selected_candidate['config_info'] = chosenf
        selected_candidate['question'] = selected_candidate['FR questions']
        selected.append(selected_candidate)

        pd.DataFrame.from_records(selected)[finaldfcols].to_csv(outfile, sep='\t', index=False)
        pbar.update()

global files, dir_path, finaldfcols
dir_path = "./outputs/"
files = os.listdir(dir_path)
files = clean_files()
finaldfcols = ['Primary Wikipedia URL', 'title', 
               'url-localized', 'question', 'model_id', 'config_info', 
               'lang', 'output_text', 'output_tokens', 
#'output_logits'
]


if __name__ == '__main__':
    main()
