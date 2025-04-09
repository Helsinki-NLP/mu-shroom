import os
import random
import json
import pathlib
import pandas as pd



def askquestion(row, printfull=True):
    if printfull:
        print("QUESTION:   " + row.question)
        print("url:   " + row['URL-es'])
        print("LLM-OUTPUT: \n\n" + row.output_text + "<END_OF_LLM_OUTPUT> \n\n")
    userans = input("Is this output to be annotated (y/n)? ").strip().lower()

    while not userans in ['y','n', 'yes', 'no']:
        print('ERROR only accepted answers are: y, n, yes, no, Y, N, YES, NO')
        userans = askquestion(printfull=False)
    return userans

def chose_answer(idx, banlist:list()=[]):
    chosenf = random.choice(list(set(files)-set(banlist)))
    row = pd.read_json(dir_path+chosenf, lines=True).iloc[idx]
    return chosenf, row

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

def main():
    badindices = []
    outfile = 'ready_for_anotation.tsv'
    if not pathlib.Path(outfile).is_file():
        finalanswers = pd.DataFrame(columns= finaldfcols)
    else:
        finalanswers = pd.read_csv(outfile, sep='\t')
        finalanswers.to_csv(outfile+'.backup', sep='\t', index=False)
        print(f'INFO: Found started file: {outfile}.')

    qnum = finalanswers.shape[0]
    print(f'INFO: Starting form question number {qnum+1}\n')
    for i in range(qnum,200):
        banlist = []; userans = 'no'; chosenf = ''
        while not userans in ['y','yes']:
            banlist.append(chosenf)
            if len(banlist) == len(files):
                row = crappyanswer(row)
                badindices.append(i)
                break
            chosenf, row = chose_answer(i, banlist)
            userans = askquestion(row)

        row['url-localized'] = row['URL-es']
        row['config_info'] = chosenf
        try: 
            row = row.drop('URL-es')
        except:
            pass
        finalanswers.loc[i] = row  
        finalanswers = finalanswers[finaldfcols]      
        finalanswers.to_csv(outfile, sep='\t', index=False)
    
    

global files, dir_path, finaldfcols
dir_path = "/home/vazquezj/git/mu-shroom/data/spanish/outputs/"
files = os.listdir(dir_path)
files = clean_files()
finaldfcols = ['url-idx', 'Primary Wikipedia URL', 'title', 
               'url-localized', 'question', 'model_id', 'config_info', 
               'lang', 'output_text', 'output_tokens', 'output_logits']


if __name__ == '__main__':
    main()