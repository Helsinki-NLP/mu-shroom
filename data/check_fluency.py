import os
import sys
import random
import pathlib
import argparse
import pandas as pd


def askquestion(row, printfull=True):
    if printfull:
        print("QUESTION:   " + row.question)
        print("url:   " + row['url-localized'])
        print("LLM-OUTPUT: \n\n" + row.output_text + "<END_OF_LLM_OUTPUT> \n\n")

    userans = input(""" Does this output contains fluency mistakes? (options: y/n/minor)
                    Use 'minor' if the output contains up to 3 minor mistakes like: orthography mistake, missing or misusing punctuation.
                    Type SAVE to save progress.
                    Type END to save your answers and come back later.\n>""")
    userans = userans.strip().lower()

    while userans not in ['y', 'n', 'yes', 'no', 'none', 'm', 'minor', 'end']:
        print('''ERROR only accepted answers are: y, n, m, yes, no, minor, Y, N, M, YES, NO, MINOR, END, end, End''')
        userans = askquestion(row, printfull=False)

    userans2 = input(""" Does this output contains factual mistakes? (options: y/n)
                    Type SAVE to save progress.
                    Type END to save your answers and come back later.\n>""")
    userans2 = userans2.strip().lower()

    while userans2 not in ['y', 'n', 'yes', 'no', 'none', 'end']:
        print('''ERROR only accepted answers are: y, n, yes, no, Y, N, M, YES, NO, END, end, End''')
        userans2 = askquestion(row, printfull=False)

    return userans, userans2


def saveprogress(finaldb, outfile, endroutine=False):
    finaldb.to_csv(outfile, sep='\t')
    if endroutine:
        sys.exit()


def main(args):
    language = args.language.lower()
    lang = lang2code[language]
    dirpath = f'./{language}/outputs/'
    files = os.listdir(dirpath)

    file = files.pop()
    dataset = pd.read_json(dirpath + file, lines=True)
    for file in files:
        tmp = pd.read_json(dirpath + file, lines=True)
        dataset = pd.concat((dataset, tmp))
        # IF YOU SAVED JSONL INSTEAD OF TSV, USE THIS:
        # with open(file, 'r') as infile:
        #     tmp = pd.read_json(infile, lines=True)
        # dataset = pd.concat((dataset, tmp))

    dataset = dataset.reset_index()
    outfile = f'{lang}_fluency-checked.tsv'

    if not pathlib.Path(outfile).is_file():
        sampled_ids = random.sample(range(len(dataset)), 100)
        finaldb = dataset[['url-localized', 'lang', 'question', 'model_id', 'output_text', 'title']].iloc[sampled_ids]
        finaldb['has_fluency_mistakes'] = None
        finaldb['has_factual_mistakes'] = None
    else:
        finaldb = pd.read_csv(outfile, sep='\t', index_col=0)
        finaldb.to_csv(outfile + '.backup', sep='\t')
        print(f'INFO: Found started file: {outfile}.')

    qnum = finaldb.has_fluency_mistakes.notna().sum() + 1
    print(f'INFO: Starting form question number {qnum} of {len(finaldb)}\n')
    for i in finaldb.index:
        if not finaldb.has_fluency_mistakes.notna().loc[i]:
            userans = askquestion(finaldb.loc[i])
            saveprogress(finaldb, outfile, ('end' in userans))

            finaldb.loc[i, 'has_fluency_mistakes'] = user2ans[userans[0]]
            finaldb.loc[i, 'has_factual_mistakes'] = user2ans[userans[1]]

    saveprogress(finaldb, outfile)


def parse_options():
    parser = argparse.ArgumentParser()
    parser.add_argument('--language', type=str,
                        help="Lanuage you will be checking for fluency",
                        default='English',
                        )

    args = parser.parse_args()
    return args


global lang2code, user2ans
lang2code = {'arabic': 'ar', 'catalan': 'ca', 'czech': 'cs', 'german': 'de', 'english': 'en',
             'euskera': 'eu', 'basque': 'eu', 'farsi': 'fa', 'persian': 'fa', 'finnish': 'fi',
             'french': 'fr', 'hindi': 'hi', 'italian': 'it', 'swedish': 'sv', 'chinese': 'zh'}

user2ans = {'yes': 'y', 'no': 'n', 'none': 'n', 'minor': 'm', 'y': 'y', 'n': 'n', 'm': 'm'}


if __name__ == '__main__':
    args = parse_options()
    main(args)
