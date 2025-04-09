import re
import requests
import pandas as pd
import time
import tqdm
from time import sleep
from bs4 import BeautifulSoup as bs


stime = time.time()
languages = ['en', 'fi', 'de', 'sv', 'zh', 'fr', 'es', 'ar', 'hi', 'it', 'eu', 'ca', 'cs']
id2lang = {'en':'English', 'fi':'Finnish', 'de':'German', 'sv':'Swedish', 
           'zh':'Chinese', 'fr':'French', 'es':'Spanish', 'ar':'Arabic', 
           'hi':'Hindi', 'it':'Italian', 'eu':'Basque', 'ca':'Catalan', 'cs':'Czech'}
urllangs = [f'Link in {id2lang[x]}' for x in languages] 
df = pd.read_csv('multiparallel_wiki_entries_fromEXCEL.tsv', sep='\t')
df['URL-idx'] = df['URL-idx'].astype(int)
#df = df.set_index('URL-idx')
#for ll in languages:
#    df[f'{ll.upper()}-idx'] = [f'{ll.upper()}-idx'].astype(int)

new_df = pd.DataFrame(columns=['URL-idx', 'Primary Wikipedia URL', 'title', 'langs']+urllangs)

for idx, row in tqdm.tqdm(df.iterrows()):
    row_url = row['Primary Wikipedia URL']
    response = requests.get(row['Primary Wikipedia URL'])
    soup = bs(response.content, 'html.parser')
    langchoice = row_url.split('://')[-1].split('.')[0]
    parallel_langs = soup.find(attrs={'id':"p-lang-btn"}).find_all('a', lang=re.compile(r"|".join(languages)))

    langslist = [langchoice]+[x['lang'] for x in parallel_langs]
    langslist = [x for x in langslist if len(x)==2]
    langslist.sort()

    new_row = pd.DataFrame(columns=['URL-idx', 'Primary Wikipedia URL','title','langs']+urllangs)
    new_row['Primary Wikipedia URL'] = [row_url]
    new_row[f'Link in {id2lang[langchoice]}'] = [row_url]
    new_row['title'] = [row.title]
    new_row['langs'] = [','.join(langslist)]
    new_row['URL-idx'] = row['URL-idx']
    for x in parallel_langs:
        lang = x['lang']
        if (lang in langslist) and (len(lang) == 2):
            new_row[f'Link in {id2lang[lang]}'] = x['href']
    
    new_row = new_row.fillna('X')
        
    new_df = pd.concat((new_df,new_row), ignore_index=True)
    new_df.to_csv('multiparallel_wiki_entries_updated.tsv',sep='\t', header=True, index=False)
    sleep(2)

new_df = new_df.set_index('URL-idx')
new_df.to_csv('multiparallel_wiki_entries_updated.tsv',sep='\t', header=True, index=True)
import ipdb; ipdb.set_trace()

